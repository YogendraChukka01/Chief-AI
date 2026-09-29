<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-blue?style=flat"/>
  <img src="https://img.shields.io/badge/License-MIT-yellow.svg?style=flat"/>
  <img src="https://img.shields.io/badge/pydantic--ai-1.0%2B-333?style=flat"/>
  <img src="https://img.shields.io/badge/opencode-native-black?style=flat"/>
  <img src="https://img.shields.io/badge/coverage-100%25-brightgreen?style=flat"/>
</p>

# Chief-AI & Chen AI Assistant

> A multi-agent operating system and terminal AI companion for software projects. Orchestrate specialized sub-agents with **Chief-AI** compiled natively into [opencode](https://opencode.ai), or converse with **Chen**, an interactive terminal AI assistant with web search, multi-provider fallback, and secure key management.

---

## 🌟 Executive Overview

**Chief-AI** provides a multi-agent framework where you interact with a single primary agent — the **Chief**. The Chief understands high-level project goals, decomposes them into structured task graphs, routes each task to domain specialist sub-agents across **11 departments and 55 sub-agents**, and synthesizes the outputs into a coherent deliverable.

**Chen** is an interactive, terminal-first conversational AI agent built on top of `pydantic-ai`. It features web search integration (via Tavily), token usage & cost tracking, multi-provider LLM support (Anthropic Claude, OpenAI, OpenRouter), and secure credential storage via OS keyrings.

```
┌────────────────────────────────────────────────────────────────────────┐
│                              Chief-AI                                  │
├───────────────────────────────────┬────────────────────────────────────┤
│           chief_ai/               │                src/                │
│ (Multi-Agent Orchestrator)        │ (pydantic-ai & Terminal Chat)      │
├───────────────────────────────────┼────────────────────────────────────┤
│ • 11 Departments & 55 Agents      │ • Chen Terminal Chat Assistant     │
│ • Deterministic Router & DAG      │ • Multi-Provider LLM Fallbacks     │
│ • Web UI & SSE Live Streaming     │ • Tavily Web Search Tools          │
│ • Memory AI & Context Retrieval   │ • Keyring Secret Store & Costs     │
└───────────────────────────────────┴────────────────────────────────────┘
```

---

## 🎯 Primary Capabilities

### 1. Chief-AI Multi-Agent Framework
- **11 Departments & 55 Specialized Sub-Agents**: Covering Executive Strategy, Engineering, Design, DevOps, QA, Documentation, Research, Marketing, Finance, Legal, and Memory AI.
- **Deterministic Routing & Task Decomposition**: `decompose(goal)` builds an ordered, dependency-aware DAG without requiring upfront LLM planning calls.
- **Dependency-Aware Parallel Execution**: Task DAGs execute independent sub-agents concurrently via `ThreadPoolExecutor` or async task runners.
- **Native opencode Compilation**: `chief generate` compiles the Python agent registry (`registry.py`) into native `.opencode/agents/*.md` and `opencode.json` files.
- **Live SSE Web UI & Mermaid DAG Viewer**: `chief serve` launches a zero-dependency web server displaying live task execution status and Mermaid DAG visualizations.
- **Memory AI**: Maintains persistent project facts, an entity knowledge graph, event history, and keyword-based context retrieval.

### 2. Chen AI Terminal Assistant
- **Interactive Terminal Chat**: Powered by `pydantic-ai` and `rich` with markdown rendering and session management.
- **Multi-Provider LLM Support**: Automatic fallback and model selection across Anthropic (Claude 3.5 Sonnet / Haiku), OpenAI (GPT-4o), and OpenRouter (DeepSeek Chat).
- **Web Search Tools**: Integrated Tavily search tool for fetching real-time web context.
- **Secure Keyring Storage**: Safely stores API keys in system keyrings (Keychain, SecretService, Credential Manager).
- **Cost & Token Estimation**: Real-time token calculation and cost tracking for prompt, completion, and cached tokens.

---

## 🏛️ The Org Chart

```
        ┌─────────────────────────────────────────┐
        │              Chief AI (primary)         │
        │     understands · decomposes · delegates│
        └───────────────┬─────────────────────────┘
                        │
        ┌───────────────┼─────────────────────────┐
        ▼               ▼                         ▼
  Executive AI     Engineering AI            Design AI
  ├ Strategy       ├ Frontend Expert         ├ UI Designer
  ├ Product        ├ Backend Expert          ├ UX Researcher
  ├ Startup        ├ Mobile Expert           ├ Graphic Designer
  └ Decision       ├ Desktop Expert          ├ Brand Designer
                   ├ AI/ML Engineer          └ Motion Designer
                   ├ Data Engineer
                   ├ API Architect           DevOps AI    QA AI
                   └ System Architect        ├ Linux      ├ Testing
                                             ├ Docker     ├ Bug Hunting
                                             ├ Kubernetes ├ Performance
                                             ├ Cloud      └ Security Audit
                                             ├ Networking
                                             └ Security

  Documentation AI · Research AI · Marketing AI · Finance AI · Legal AI · Memory AI
```

---

## 🛠️ Tech Stack

- **Language & Runtime**: Python 3.12+ · `uv` / `pip`
- **Agent Orchestration**: `pydantic-ai` · `argparse` · `typer` · `rich`
- **Execution Runtimes**: `opencode` (sub-agents) · `ThreadPoolExecutor` (parallel scheduling) · Standard Library HTTP/SSE
- **Model Providers**: Anthropic · OpenAI · OpenRouter
- **Tools & Security**: Tavily Search · `keyring` (Secure Storage) · `pydantic-settings`
- **Testing & Quality**: `pytest` · `pytest-asyncio` · `ruff` · `mypy`

---

## ⚡ Quick Start & Installation

### Prerequisites
- Python 3.12+
- `uv` (recommended) or `pip`

### 1. Installation

```bash
# Clone repository
git clone https://github.com/YogendraChukka01/Chief-AI.git
cd Chief-AI

# Install dependencies
uv sync --extra dev
# or: pip install -e ".[dev]"
```

### 2. Using Chief AI Orchestrator

```bash
# Preview plan decomposition (no LLM calls required)
uv run python -m chief_ai.cli plan "Build a real-time web chat application"

# Execute plan using MockExecutor (instant preview)
uv run python -m chief_ai.cli run "Build a real-time web chat application"

# Execute plan with parallel task execution
uv run python -m chief_ai.cli run "Build a real-time web chat application" --parallel

# Execute using real opencode sub-agents
uv run python -m chief_ai.cli run "Build a real-time web chat application" --opencode

# Launch live web UI & DAG viewer
uv run python -m chief_ai.cli serve --port 8000
# Open http://127.0.0.1:8000 in your browser

# Re-generate .opencode agent files from the registry
uv run python -m chief_ai.cli generate

# List all departments and sub-agents
uv run python -m chief_ai.cli list
```

### 3. Using Chen Terminal Assistant

```bash
# Run onboarding setup (API keys and configuration)
uv run chen onboard

# Launch interactive terminal session
uv run chen

# View or update configuration settings
uv run chen config list
uv run chen config set openai_api_key "sk-..."
```

---

## 📐 System Architecture

```
Chief-AI/
├── chief_ai/                   # Chief AI Multi-Agent Framework
│   ├── core/
│   │   ├── types.py            # Department, SubAgent, Task, Result, Permission
│   │   ├── registry.py         # SINGLE SOURCE OF TRUTH: 11 depts + 55 agents
│   │   ├── router.py           # decompose(goal) -> tasks ; route(text) -> agent
│   │   ├── chief.py            # ChiefAI orchestrator: plan → dispatch → synthesize
│   │   └── memory.py           # MemoryAI: facts, graph, history, retrieval
│   ├── integrations/
│   │   ├── opencode_generator.py# registry -> .opencode/agents/*.md + opencode.json
│   │   └── opencode_runner.py  # Executor that shells out to `opencode run`
│   ├── cli.py                  # `chief plan | run | generate | list | serve`
│   └── web.py                  # SSE live stream & Mermaid DAG server
├── src/                        # Agentic & Terminal Assistant Libraries
│   ├── libagentic/             # Provider models, keyring store, tools & logging
│   ├── libchatinterface/       # Chat session management, cost tracking, markdown UI
│   └── appclis/                # Typer CLI wrappers for chief and chen
├── PROJECT_ANALYSIS.md         # Full architectural analysis & roadmap
├── .opencode/                  # Generated opencode sub-agent markdown files
└── tests/                      # Pytest test suite
```

---

## 🧪 Testing & Verification

Run the comprehensive test suite with `pytest`:

```bash
uv run --extra dev pytest
```

The test suite covers:
- Registry completeness & unique sub-agent IDs across all 11 departments
- Deterministic routing and tag/intent matching logic
- Opencode sub-agent generator and YAML frontmatter validation
- Parallel task DAG scheduling and result synthesis
- Web SSE live streaming endpoints and static asset delivery
- Provider model selection and cost calculations

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
