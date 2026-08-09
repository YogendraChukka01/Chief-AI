<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat"/>
  <img src="https://img.shields.io/badge/pydantic--ai-333?style=flat"/>
  <img src="https://img.shields.io/badge/opencode-native-black?style=flat"/>
</p>

# Chief-AI

> A single **Chief AI** that orchestrates a team of **specialized sub-agents** — built as a Python framework that compiles into native [opencode](https://opencode.ai) agents.

Chief-AI is a multi-agent operating system for software projects. You interact with exactly one agent — the **Chief** — which understands your goal, decomposes it into tasks, delegates each task to the most qualified specialist, and returns a single, coherent result. Every specialist runs as a real **opencode sub-agent**, so there are no external LLM keys to manage from Python.

## Project Snapshot

```
┌──────────────────────────────────────────────────────┐
│ 🏗️ Chief-AI                                          │
│                                                      │
│ Multi-agent orchestrator for software projects       │
│                                                      │
│ AI        Backend      DevOps       QA              │
│ Python    pydantic-ai  Testing      pytest           │
│ 11 Depts  opencode     SSE Stream   Registry         │
│ 55 Agents Web UI       Memory AI    MockExecutor     │
│                                                      │
│ Status: Active  License: MIT                          │
└──────────────────────────────────────────────────────┘
```

## How It Works

```
Goal → decompose() → Ordered Task List
                       ↓
                     Router (tags + intent matching)
                       ↓
     Department-sorted dispatch → ThreadPoolExecutor
                       ↓
         OpencodeRunner (real sub-agents) or MockExecutor
                       ↓
          MemoryAI context injected per task
                       ↓
                 Synthesize → coherent result
```

---

## The Org Chart

```
        ┌─────────────────────────────────────────┐
        │              Chief AI (primary)           │
        │     understands · decomposes · delegates  │
        └───────────────┬───────────────────────────┘
                        │  @mention / Task tool
        ┌───────────────┼───────────────────────────┐
        ▼               ▼                           ▼
  Executive AI     Engineering AI              Design AI
  ├ Strategy       ├ Frontend Expert           ├ UI Designer
  ├ Product        ├ Backend Expert            ├ UX Researcher
  ├ Startup        ├ Mobile Expert             ├ Graphic Designer
  └ Decision       ├ Desktop Expert            ├ Brand Designer
                   ├ AI/ML Engineer            └ Motion Designer
                   ├ Data Engineer
                   ├ API Architect             DevOps AI    QA AI
                   └ System Architect          ├ Linux      ├ Testing
                                               ├ Docker     ├ Bug Hunting
                                               ├ Kubernetes ├ Performance
                                               ├ Cloud      └ Security Audit
                                               ├ Networking
                                               └ Security

  Documentation AI · Research AI · Marketing AI · Finance AI · Legal AI · Memory AI
```

---

## Why Chief-AI?

| Problem | Chief-AI's answer |
| --- | --- |
| One model can't be an expert at everything | A department per domain, a specialist per concern |
| Context gets lost between tools | A single orchestrator retains the goal end-to-end |
| Agents need a host runtime | Compiles to **opencode sub-agents** — no bespoke infra |
| Config drift between code and agents | The Python registry is the **single source of truth** |

---

## Feature overview

- **11 departments, 55 sub-agents** covering the full product lifecycle.
- **Deterministic routing** — `decompose()` turns a goal into an ordered, department-sorted task list.
- **Two execution backends** — `MockExecutor` for instant previews, `OpencodeRunner` for live sub-agent execution.
- **Persistent memory** — long-term facts, a knowledge graph, project history, and keyword context retrieval.
- **Reproducible artifacts** — `chief generate` emits every `.opencode/agents/*.md` and `opencode.json` from the registry.
- **Tested** — registry, router, and generator covered by `pytest`.

---

## Tech Stack

### Core
Python 3.10+ · pydantic-ai · argparse · ThreadPoolExecutor · Standard library (HTTP server for web UI)

### AI / Agent Runtime
opencode (native sub-agents) · LLM providers (via opencode)

### Orchestration
Registry-driven routing · Deterministic task decomposition · Dependency-aware parallel scheduling · SSE streaming for web UI

### Memory
Persistent facts · Knowledge graph · Project history · Keyword-based context retrieval

### Engineering
Git · pytest · Mermaid (diagram rendering) · Python packaging (setuptools)

---

## Engineering Decisions

### Why Python?
The orchestration logic (decomposition, routing, scheduling, synthesis) is deterministic and fast — it doesn't need an LLM. Python's data classes, type hints, and `ThreadPoolExecutor` make the registry and router clean and testable without pulling in a heavy framework.

### Why opencode as the execution backend?
Each specialist is generated as a native opencode sub-agent (`.md` file + `opencode.json`). This means:
- No custom runtime to maintain
- Real LLM execution via opencode's infrastructure
- Automatic permission scoping per agent
- The Python registry is the only source of truth

### Why a registry-driven approach?
All 55 agents are defined as data in `registry.py`. This makes the system inspectable (`chief list`), testable (`test_registry.py`), and reproducible (`chief generate` rebuilds all opencode files from the registry).

### Why MockExecutor?
Allows instant, deterministic previews of execution plans without making LLM calls. Perfect for testing the orchestration logic and for live UI demos.

---

## Installation

Requires Python 3.10+.

```bash
git clone https://github.com/YogendraChukka01/Chief-AI.git
cd Chief-AI
pip install -e ".[dev]"
```

To execute sub-agents for real, install [opencode](https://opencode.ai/docs/install)
and ensure the `opencode` binary is on your `PATH`.

---

## Quick start

```bash
# 1. Preview how the Chief decomposes a goal (no LLM calls)
chief plan "Build the next version of my portfolio"

# 2. Execute with the mock executor (instant, deterministic)
chief run "Build the next version of my portfolio"

# 3. Execute with REAL opencode sub-agents
chief run "Build the next version of my portfolio" --opencode

# 4. Run teams of independent agents concurrently
chief run "Build the next version of my portfolio" --parallel

# 5. Launch the live-plan web UI (zero dependencies)
chief serve --port 8000
# open http://127.0.0.1:8000

# 6. (Re)generate the .opencode/ agent files from the registry
chief generate

# 7. Inspect the org chart
chief list
```

After `chief generate`, open the project in opencode and switch to the **chief**
primary agent (Tab, or `@chief`). It will delegate work to the `@<agent>`
specialists automatically.

### Web UI

`chief serve` starts a small web server (standard library only — no extra
dependencies) that:

- renders the goal's **dependency DAG** with [mermaid](https://mermaid.js.org),
- **streams execution live** over Server-Sent Events as the Chief dispatches each
  sub-agent, updating task cards from *pending → running → done*.

Open `http://127.0.0.1:8000`, type a goal, and click **Show Plan** then **Run Live**.

### Programmatic usage

```python
from chief_ai import ChiefAI, MockExecutor

chief = ChiefAI(executor=MockExecutor())
plan = chief.plan("Ship a v2 of the marketing site")
print(plan.render())

result = chief.execute("Ship a v2 of the marketing site")
print(result)
```

---

## Architecture

```
Chief-AI/
├── chief_ai/
│   ├── core/
│   │   ├── types.py        # Department, SubAgent, Task, Result, Permission
│   │   ├── registry.py     # SINGLE SOURCE OF TRUTH: 11 depts + 55 agents
│   │   ├── router.py       # decompose(goal) -> tasks ; route(text) -> agent
│   │   ├── chief.py        # ChiefAI orchestrator: plan → dispatch → synthesize
│   │   └── memory.py       # MemoryAI: facts, graph, history, retrieval
│   ├── integrations/
│   │   ├── opencode_generator.py  # registry -> .opencode/agents/*.md + opencode.json
│   │   └── opencode_runner.py     # Executor that shells out to `opencode run`
│   └── cli.py              # `chief plan | run | generate | list`
├── .opencode/
│   ├── agents/             # chief.md (primary) + one .md per specialist (generated)
│   └── opencode.json       # wires the chief primary agent
└── tests/
```

### Execution model

1. **Python owns the logic.** The `ChiefAI` orchestrator plans, routes, dispatches,
   and synthesizes using only the local registry — no network calls.
2. **opencode owns the execution.** Each specialist is a generated sub-agent with
   scoped permissions. The `chief` primary agent invokes them via the Task tool /
   `@mention`, so the actual LLM work happens inside opencode.
3. **One source of truth.** Edit agents in `chief_ai/core/registry.py`, then run
   `chief generate` to rebuild every `.opencode/` file.

---

## The org chart

| Department | Sub-agents |
| --- | --- |
| **Executive AI** | Strategy · Product Management · Startup Advisor · Decision Engine |
| **Engineering AI** | Frontend · Backend · Mobile · Desktop · AI/ML · Data · API Architect · System Architect |
| **Design AI** | UI · UX Researcher · Graphic · Brand · Motion |
| **DevOps AI** | Linux · Docker · Kubernetes · Cloud · Networking · Security |
| **QA AI** | Testing · Bug Hunting · Performance · Security Audit |
| **Documentation AI** | PRDs · READMEs · API Docs · Technical Writing |
| **Research AI** | AI Research · Market · Competitor · Patent · Academic |
| **Marketing AI** | SEO · LinkedIn · GitHub · Portfolio · Social Media · Launch Strategy |
| **Finance AI** | Budgeting · Pricing · Revenue · Startup Finance |
| **Legal AI** | Licenses · Privacy · Terms · Compliance |
| **Memory AI** | Long-term · Knowledge Graph · History · Context Retrieval · Learning Engine |

---

## Extending Chief-AI

All agents live in `chief_ai/core/registry.py`. To add a specialist:

```python
_Spec("eng-game", "Game Engine Expert", "Builds real-time game engines.",
      ["game", "engine", "unity", "unreal", "godot"])
```

then:

```bash
chief generate   # rebuilds .opencode/agents/eng-game.md
```

Permissions and tools are inherited from the parent department preset and can be
overridden per-agent. See `chief_ai/core/registry.py` for the full schema.

---

## Testing

```bash
pytest
```

Covers registry completeness (11 departments, unique IDs, valid permissions),
router accuracy (intent → correct agent, build-goal expansion, department ordering),
and generator validity (frontmatter parses, chief is primary with task access).

---

## Roadmap

- [x] Plug `MemoryAI` retrieval into the Chief's prompt context.
- [x] Per-agent `model` overrides in the registry (and `CHIEF_MODEL` default).
- [x] Parallel dispatch with dependency-aware scheduling.
- [x] Web/streaming UI for live plan visualization.

---

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feat/...`).
3. Make your change in `chief_ai/core/registry.py` (or the relevant module) and
   run `chief generate` if you touched agents.
4. Ensure `pytest` passes.
5. Open a pull request.

---

## License

This project is licensed under the MIT License — see the `LICENSE` file for details.

---

## Acknowledgements

Built on top of [opencode](https://opencode.ai) multi-agent subagents.

---

<h3 align="center">

```
Built by Yogi

  Build.  Learn.  Ship.  Iterate.
```

</h3>

<p align="center">
  <img src="https://img.shields.io/badge/—%20AI%20×%20Software%20×%20Product%20×%20Open%20Source-0d1117?style=for-the-badge&labelColor=0d1117&color=7c3aed"/>
</p>
