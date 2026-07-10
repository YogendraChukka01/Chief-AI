"""Zero-dependency web UI for live Chief AI plan visualization.

Serves a single-page UI that:
  * renders the goal's dependency DAG (via mermaid.js from a CDN),
  * streams execution live over Server-Sent Events as the Chief dispatches
    each sub-agent.

Only the Python standard library is used, so there are no extra dependencies.
"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Optional
from urllib.parse import parse_qs, urlparse

from .core.chief import ChiefAI
from .core.memory import MemoryAI
from .integrations.opencode_runner import OpencodeRunner

INDEX_HTML = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Chief AI — Live Plan</title>
<script src="https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.min.js"></script>
<style>
  :root { --bg:#0d1117; --fg:#e6edf3; --muted:#8b949e; --card:#161b22;
          --pending:#6e7681; --run:#d29922; --done:#2ea043; --accent:#58a6ff; }
  * { box-sizing: border-box; }
  body { margin:0; font:14px/1.5 system-ui, sans-serif; background:var(--bg); color:var(--fg); }
  header { padding:16px 20px; border-bottom:1px solid #21262d; }
  h1 { margin:0; font-size:18px; }
  .controls { display:flex; gap:8px; flex-wrap:wrap; align-items:center; padding:14px 20px; }
  input[type=text] { flex:1; min-width:260px; padding:9px 11px; border-radius:6px;
        border:1px solid #30363d; background:var(--card); color:var(--fg); }
  button { padding:9px 14px; border-radius:6px; border:1px solid #30363d;
        background:#21262d; color:var(--fg); cursor:pointer; }
  button.primary { background:var(--accent); color:#0d1117; border-color:var(--accent); }
  label.chk { color:var(--muted); display:flex; gap:6px; align-items:center; }
  main { display:grid; grid-template-columns: 1fr 1fr; gap:16px; padding:0 20px 24px; }
  @media (max-width:900px){ main { grid-template-columns:1fr; } }
  .panel { background:var(--card); border:1px solid #21262d; border-radius:10px; padding:14px; }
  .panel h2 { margin:0 0 10px; font-size:14px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }
  #diagram { display:flex; justify-content:center; }
  .task { border:1px solid #21262d; border-left-width:4px; border-radius:8px;
        padding:10px 12px; margin-bottom:10px; background:#0d1117; }
  .task .name { font-weight:600; }
  .task .dept { color:var(--muted); font-size:12px; }
  .task.pending { border-left-color:var(--pending); }
  .task.running { border-left-color:var(--run); }
  .task.done { border-left-color:var(--done); }
  .badge { float:right; font-size:11px; padding:2px 8px; border-radius:999px;
        background:#21262d; color:var(--muted); }
  .task.running .badge { background:var(--run); color:#0d1117; }
  .task.done .badge { background:var(--done); color:#0d1117; }
  .task pre { white-space:pre-wrap; word-break:break-word; margin:8px 0 0; color:var(--fg); }
  #result { white-space:pre-wrap; }
  .hint { color:var(--muted); font-size:12px; }
</style>
</head>
<body>
<header><h1>Chief AI — Live Plan Visualizer</h1></header>
<div class="controls">
  <input id="goal" type="text" placeholder="Describe a goal, e.g. Build the next version of my portfolio" />
  <button class="primary" id="planBtn">Show Plan</button>
  <button id="runBtn">Run Live</button>
  <label class="chk"><input type="checkbox" id="parallel" /> parallel</label>
</div>
<main>
  <div class="panel"><h2>Dependency Graph</h2><div id="diagram"><span class="hint">Enter a goal and click Show Plan.</span></div></div>
  <div class="panel"><h2>Tasks</h2><div id="tasks"><span class="hint">No tasks yet.</span></div></div>
</main>
<div class="panel" style="margin:0 20px 24px;"><h2>Integrated Result</h2><pre id="result"><span class="hint">Appears when execution completes.</span></pre></div>

<script>
  mermaid.initialize({ startOnLoad:false, theme:"dark", securityLevel:"loose" });
  const $ = (id) => document.getElementById(id);
  let taskState = {};

  function buildGraph(plan){
    let g = "graph TD\\n";
    plan.tasks.forEach(t => { g += `${t.id}["${t.name}"]\\n`; });
    plan.tasks.forEach(t => { (t.dependencies||[]).forEach(d => { g += `${d} --> ${t.id}\\n`; }); });
    return g;
  }
  async function renderDiagram(plan){
    const el = $("diagram"); el.innerHTML = '<div class="mermaid">' + buildGraph(plan) + '</div>';
    try { await mermaid.run({ querySelector:".mermaid" }); }
    catch(e){ el.textContent = "graph render failed"; }
  }
  function renderTasks(){
    const el = $("tasks");
    const ids = Object.keys(taskState);
    if(!ids.length){ el.innerHTML = '<span class="hint">No tasks yet.</span>'; return; }
    el.innerHTML = ids.map(id => {
      const t = taskState[id];
      const cls = t.status;
      const label = t.status === "running" ? "running" : t.status === "done" ? "done" : "pending";
      const body = t.content ? `<pre>${escapeHtml(t.content)}</pre>` : "";
      return `<div class="task ${cls}"><span class="badge">${label}</span>
        <div class="name">${escapeHtml(t.name)}</div>
        <div class="dept">${escapeHtml(t.department||"")}</div>${body}</div>`;
    }).join("");
  }
  function escapeHtml(s){ return (s||"").replace(/[&<>]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;"}[c])); }

  async function showPlan(){
    const goal = $("goal").value.trim(); if(!goal) return;
    const r = await fetch("/api/plan?goal=" + encodeURIComponent(goal));
    const plan = await r.json();
    taskState = {};
    plan.tasks.forEach(t => { taskState[t.id] = { name:t.name, department:t.department, status:"pending", content:"" }; });
    renderDiagram(plan); renderTasks();
  }
  function runLive(){
    const goal = $("goal").value.trim(); if(!goal) return;
    const parallel = $("parallel").checked ? "1" : "0";
    taskState = {}; renderTasks();
    const es = new EventSource("/api/run?goal=" + encodeURIComponent(goal) + "&parallel=" + parallel);
    es.onmessage = (ev) => {
      const e = JSON.parse(ev.data);
      if(e.type === "plan"){
        e.plan.tasks.forEach(t => { taskState[t.id] = { name:t.name, department:t.department, status:"pending", content:"" }; });
        renderDiagram(e.plan); renderTasks();
      } else if(e.type === "task_start"){
        if(taskState[e.task_id]){ taskState[e.task_id].status = "running"; renderTasks(); }
      } else if(e.type === "task_done"){
        if(taskState[e.task_id]){ taskState[e.task_id].status = "done"; taskState[e.task_id].content = e.content; renderTasks(); }
      } else if(e.type === "done"){
        $("result").textContent = e.result; es.close();
      }
    };
    es.onerror = () => es.close();
  }
  $("planBtn").onclick = showPlan;
  $("runBtn").onclick = runLive;
  $("goal").addEventListener("keydown", e => { if(e.key === "Enter") showPlan(); });
</script>
</body>
</html>
"""


class _Handler(BaseHTTPRequestHandler):
    chief: ChiefAI

    def _send(self, code: int, body: bytes, content_type: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path in ("/", "/index.html"):
            self._send(200, INDEX_HTML.encode("utf-8"), "text/html; charset=utf-8")
            return
        if parsed.path == "/api/plan":
            self._handle_plan(parse_qs(parsed.query))
            return
        if parsed.path == "/api/run":
            self._handle_run(parse_qs(parsed.query))
            return
        self._send(404, b"not found", "text/plain")

    def _handle_plan(self, qs: dict) -> None:
        goal = (qs.get("goal") or [""])[0]
        plan = self.chief.plan(goal)
        payload = json.dumps(
            {
                "goal": plan.goal,
                "tasks": [
                    {
                        "id": t.id,
                        "department": t.department,
                        "sub_agent": t.sub_agent,
                        "name": _agent_name(t.sub_agent),
                        "dependencies": list(t.dependencies),
                    }
                    for t in plan.tasks
                ],
            }
        ).encode("utf-8")
        self._send(200, payload, "application/json")

    def _handle_run(self, qs: dict) -> None:
        goal = (qs.get("goal") or [""])[0]
        parallel = (qs.get("parallel") or ["0"])[0] == "1"
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        for event in self.chief.stream(goal, parallel=parallel):
            self.wfile.write(f"data: {json.dumps(event)}\n\n".encode("utf-8"))
            self.wfile.flush()

    def log_message(self, *args) -> None:  # silence default logging
        pass


def _agent_name(sub_id: Optional[str]) -> str:
    from .core.registry import get_sub_agent

    if not sub_id:
        return "?"
    try:
        return get_sub_agent(sub_id).name
    except KeyError:
        return "?"


def make_server(host: str = "127.0.0.1", port: int = 8000, use_opencode: bool = False) -> ThreadingHTTPServer:
    executor = OpencodeRunner() if use_opencode else None
    chief = ChiefAI(memory=MemoryAI(), executor=executor)

    class Handler(_Handler):
        pass

    Handler.chief = chief
    return ThreadingHTTPServer((host, port), Handler)
