# Chief-AI

A **single Chief AI** that manages a team of **specialized sub-agents**. You interact
only with the Chief; it understands your goal, decomposes it into tasks, delegates
each to the right specialist, and synthesizes one coherent response.

The system is implemented as a **Python framework** (`chief_ai`) that owns the
architecture, orchestration, and memory. It **generates opencode-native agents** so
each specialist runs as a real **opencode sub-agent** — no external LLM keys required
in Python.

```
Chief AI (chief.md, primary agent)
│
├── Executive AI      (Strategy, Product, Startup Advisor, Decision Engine)
├── Engineering AI    (Frontend, Backend, Mobile, Desktop, AI/ML, Data, API, System)
├── Design AI         (UI, UX, Graphic, Brand, Motion)
├── DevOps AI         (Linux, Docker, Kubernetes, Cloud, Networking, Security)
├── QA AI             (Testing, Bug Hunting, Performance, Security Audit)
├── Documentation AI  (PRDs, READMEs, API Docs, Technical Writing)
├── Research AI       (AI, Market, Competitor, Patent, Academic)
├── Marketing AI      (SEO, LinkedIn, GitHub, Portfolio, Social, Launch)
├── Finance AI        (Budgeting, Pricing, Revenue, Startup Finance)
├── Legal AI          (Licenses, Privacy, Terms, Compliance)
└── Memory AI         (Long-term, Knowledge Graph, History, Context, Learning)
```

## Architecture

- `chief_ai/core/registry.py` — **single source of truth**: all 11 departments and 55 sub-agents.
- `chief_ai/core/router.py` — `decompose(goal)` → routed tasks; `route(text)` → best agent.
- `chief_ai/core/chief.py` — `ChiefAI` orchestrator: plan → dispatch → synthesize.
- `chief_ai/core/memory.py` — `MemoryAI`: long-term store, knowledge graph, history, retrieval.
- `chief_ai/integrations/opencode_generator.py` — emits `.opencode/agents/*.md` + `opencode.json`.
- `chief_ai/integrations/opencode_runner.py` — runs sub-agents via the `opencode` CLI.

## Install

```bash
pip install -e ".[dev]"
```

## Usage

```bash
# Preview how the Chief would decompose a goal (no execution)
chief plan "Build the next version of my portfolio"

# Execute a goal using the mock executor (no LLM calls)
chief run "Build the next version of my portfolio"

# Execute using REAL opencode sub-agents (requires `opencode` on PATH)
chief run "Build the next version of my portfolio" --opencode

# Generate the opencode agent files into .opencode/
chief generate

# List every department and sub-agent
chief list
```

After `chief generate`, open the project in opencode and switch to the **chief**
primary agent (Tab / `@chief`). It will delegate work to the `@<agent>` specialists.

## Extending

Add or edit agents in `chief_ai/core/registry.py`, then re-run `chief generate` to
rebuild the `.opencode/` artifacts. The Python registry stays the single source of truth.

## Tests

```bash
pytest
```
