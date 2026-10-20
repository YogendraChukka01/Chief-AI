"""Command-line interface for the Chief AI system.

Usage:
    chief plan "build the next version of my portfolio"
    chief run  "build the next version of my portfolio" [--opencode]
    chief generate [--target .]
    chief list
    chief memory list
    chief memory forget <key>
    chief memory clear
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys

# Force UTF-8 on Windows before any output is written.
# This fixes UnicodeEncodeError with characters like (arrow) on cp1252 terminals.
if sys.platform == "win32":
    os.environ.setdefault("PYTHONUTF8", "1")
    if hasattr(sys.stdout, "reconfigure"):
        with contextlib.suppress(io.UnsupportedOperation, AttributeError):
            sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        with contextlib.suppress(io.UnsupportedOperation, AttributeError):
            sys.stderr.reconfigure(encoding="utf-8")

from .core.chief import ChiefAI, MockExecutor
from .core.memory import MemoryAI
from .core.registry import DEPARTMENTS, list_sub_agents
from .integrations.opencode_generator import generate
from .integrations.opencode_runner import OpencodeRunner
from .web import make_server


def _cmd_plan(args: argparse.Namespace) -> int:
    chief = ChiefAI(executor=MockExecutor())
    plan = chief.plan(args.goal)
    if args.json:
        print(json.dumps({"goal": plan.goal, "tasks": [vars(t) for t in plan.tasks]}, indent=2))
    else:
        print(plan.render())
    return 0


def _cmd_run(args: argparse.Namespace) -> int:
    executor = OpencodeRunner() if args.opencode else MockExecutor()
    chief = ChiefAI(executor=executor)
    print(chief.execute(args.goal, parallel=args.parallel))
    return 0


def _cmd_generate(args: argparse.Namespace) -> int:
    written = generate(args.target)
    print(f"Generated {len(written)} file(s):")
    for path in written:
        print(f"  {path}")
    return 0


def _cmd_list(args: argparse.Namespace) -> int:
    for dept in DEPARTMENTS:
        print(f"{dept.name}  ({len(dept.sub_agents)} agents)")
        for sub in dept.sub_agents:
            print(f"  - @{sub.id:<20} {sub.name}: {sub.description}")
    print(f"\nTotal: {len(list_sub_agents())} sub-agents across {len(DEPARTMENTS)} departments.")
    return 0


def _cmd_serve(args: argparse.Namespace) -> int:
    server = make_server(host=args.host, port=args.port, use_opencode=args.opencode)
    url = f"http://{args.host}:{args.port}/"
    print(f"Chief AI web UI running at {url}  (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
    return 0


def _cmd_memory_list(args: argparse.Namespace) -> int:
    mem = MemoryAI(path=args.path)
    facts = mem._state.facts
    cats = mem._state.categories
    g = mem.graph()

    print(f"Memory store ({mem.path}): {len(facts)} fact(s)")
    if facts:
        for k, v in facts.items():
            cat_str = f" [{cats[k]}]" if k in cats else ""
            print(f"  - {k}{cat_str}: {v}")
    if g["nodes"]:
        print(f"\nKnowledge Graph: {len(g['nodes'])} node(s), {len(g['edges'])} edge(s)")
        for n in g["nodes"]:
            print(f"  - Node {n['id']} ({n['kind']}): {n['label']}")
    return 0


def _cmd_memory_forget(args: argparse.Namespace) -> int:
    mem = MemoryAI(path=args.path)
    if mem.forget(args.key):
        print(f"Forgot fact with key: '{args.key}'")
    else:
        print(f"Key not found in memory: '{args.key}'")
    return 0


def _cmd_memory_clear(args: argparse.Namespace) -> int:
    mem = MemoryAI(path=args.path)
    mem.clear()
    print(f"Cleared all memory from store ({mem.path}).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="chief", description="Chief AI orchestrator CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_plan = sub.add_parser("plan", help="Decompose a goal into a routed plan (no execution)")
    p_plan.add_argument("goal")
    p_plan.add_argument("--json", action="store_true")
    p_plan.set_defaults(func=_cmd_plan)

    p_run = sub.add_parser("run", help="Plan and execute a goal")
    p_run.add_argument("goal")
    p_run.add_argument("--opencode", action="store_true", help="Use real opencode sub-agents")
    p_run.add_argument("--parallel", action="store_true", help="Run independent tasks concurrently")
    p_run.set_defaults(func=_cmd_run)

    p_gen = sub.add_parser("generate", help="Emit .opencode agent files and opencode.json")
    p_gen.add_argument("--target", default=".")
    p_gen.set_defaults(func=_cmd_generate)

    p_list = sub.add_parser("list", help="List departments and sub-agents")
    p_list.set_defaults(func=_cmd_list)

    p_serve = sub.add_parser("serve", help="Launch the live-plan web UI")
    p_serve.add_argument("--host", default="127.0.0.1")
    p_serve.add_argument("--port", type=int, default=8000)
    p_serve.add_argument("--opencode", action="store_true", help="Use real opencode sub-agents")
    p_serve.set_defaults(func=_cmd_serve)

    p_mem = sub.add_parser("memory", help="Inspect or manage Chief AI persistent memory")
    p_mem.add_argument(
        "--path", default=".chief_memory/memory.json", help="Path to memory store file"
    )
    mem_sub = p_mem.add_subparsers(dest="memory_command", required=True)

    p_mem_list = mem_sub.add_parser("list", help="List facts and knowledge graph summary")
    p_mem_list.set_defaults(func=_cmd_memory_list)

    p_mem_forget = mem_sub.add_parser("forget", help="Remove a fact from memory")
    p_mem_forget.add_argument("key", help="Fact key to remove")
    p_mem_forget.set_defaults(func=_cmd_memory_forget)

    p_mem_clear = mem_sub.add_parser("clear", help="Clear all stored memory")
    p_mem_clear.set_defaults(func=_cmd_memory_clear)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
