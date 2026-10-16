import json
import threading
import urllib.parse
import urllib.request

from chief_ai.core.chief import ChiefAI, MockExecutor
from chief_ai.web import make_server

GOAL = "Build the next version of my portfolio"


def _event_types(goal: str, parallel: bool) -> list[str]:
    chief = ChiefAI(executor=MockExecutor())
    return [e["type"] for e in chief.stream(goal, parallel=parallel)]


def test_stream_sequential_event_sequence() -> None:
    types = _event_types(GOAL, parallel=False)
    assert types[0] == "plan"
    assert types[-1] == "done"
    # plan, N*(start+done), done
    assert types.count("task_start") == types.count("task_done")
    assert types.count("task_start") >= 5


def test_stream_parallel_yields_same_final_result() -> None:
    sequential = ChiefAI(executor=MockExecutor()).execute(GOAL, parallel=False)
    parallel = ChiefAI(executor=MockExecutor()).execute(GOAL, parallel=True)
    # Both must contain the same set of specialist sections.
    for name in ("Strategy", "Frontend Expert", "Launch Strategy"):
        assert name in sequential and name in parallel


def test_web_plan_and_index_endpoints() -> None:
    server = make_server(host="127.0.0.1", port=0)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        base = f"http://127.0.0.1:{port}"
        with urllib.request.urlopen(f"{base}/api/plan?goal={urllib.parse.quote(GOAL)}") as r:
            assert r.status == 200
            data = json.loads(r.read())
        assert data["goal"] == GOAL
        assert any(tk["sub_agent"] == "eng-frontend" for tk in data["tasks"])

        with urllib.request.urlopen(f"{base}/") as r:
            assert r.status == 200
            content = r.read()
            assert b"Chief AI" in content
            assert b"mTotal" in content
            assert b"taskSearch" in content
    finally:
        server.shutdown()
        t.join(timeout=2)


def test_web_run_sse_streams_events() -> None:
    server = make_server(host="127.0.0.1", port=0)
    port = server.server_address[1]
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    try:
        base = f"http://127.0.0.1:{port}"
        url = f"{base}/api/run?goal={urllib.parse.quote(GOAL)}&parallel=0"
        with urllib.request.urlopen(url) as r:
            raw = r.read().decode("utf-8")
        events = [json.loads(line[6:]) for line in raw.split("\n\n") if line.startswith("data: ")]
        assert events[0]["type"] == "plan"
        assert events[-1]["type"] == "done"
        done_events = [e for e in events if e["type"] == "task_done"]
        assert len(done_events) > 0
        for e in done_events:
            assert "duration_seconds" in e
    finally:
        server.shutdown()
        t.join(timeout=2)
