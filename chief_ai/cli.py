"""Command-line interface for the Chief AI system.

Usage:
    chief plan "build the next version of my portfolio"
    chief run  "build the next version of my portfolio" [--opencode]
    chief generate [--target .]
    chief list
    chief memory list
    chief memory query "database"
    chief memory add <key> <value> [--tag TAG] [--category CAT]
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


# -- memory commands ---------------------------------------------------
def _cmd_memory_list(args: argparse.Namespace) -> int:
    mem = MemoryAI()
    facts = mem.list_facts(tag=args.tag, category=args.category)
    if not facts:
        print("No memory facts found.")
        return 0

    print(f"Memory Facts ({len(facts)}):")
    for k, v in facts.items():
        meta = mem.get_fact_meta(k) or {}
        meta_str = ""
        if meta.get("tags") or meta.get("category"):
            tags = ", ".join(meta.get("tags", []))
            cat = meta.get("category") or "-"
            meta_str = f" [tags: {tags} | category: {cat}]"
        print(f"  - {k}: {v}{meta_str}")
    return 0


def _cmd_memory_query(args: argparse.Namespace) -> int:
    mem = MemoryAI()
    hits = mem.retrieve(
        query=args.query,
        limit=args.limit,
        tag=args.tag,
        category=args.category,
    )
    if not hits:
        print("No matching memory entries found.")
        return 0

    print(f"Query Results ({len(hits)}):")
    for hit in hits:
        print(f"  - {hit}")
    return 0


def _cmd_memory_add(args: argparse.Namespace) -> int:
    mem = MemoryAI()
    tags = [t.strip() for t in args.tag.split(",")] if args.tag else None
    mem.remember(key=args.key, value=args.value, tags=tags, category=args.category)
    print(f"Remembered fact: '{args.key}'")
    return 0


def _cmd_memory_remove(args: argparse.Namespace) -> int:
    mem = MemoryAI()
    existed = mem.forget(args.key)
    if existed:
        print(f"Removed fact: '{args.key}'")
    else:
        print(f"Fact '{args.key}' not found in memory.")
    return 0


def _cmd_memory_clear(args: argparse.Namespace) -> int:
    mem = MemoryAI()
    mem.clear()
    print("Memory cleared.")
    return 0


def _cmd_memory_export(args: argparse.Namespace) -> int:
    mem = MemoryAI()
    mem.export_memory(args.file)
    print(f"Exported memory to '{args.file}'.")
    return 0


def _cmd_memory_import(args: argparse.Namespace) -> int:
    mem = MemoryAI()
    try:
        mem.import_memory(args.file, merge=not args.overwrite)
        print(f"Imported memory from '{args.file}'.")
    except Exception as err:
        print(f"Failed to import memory: {err}")
        return 1
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

    # memory subcommands
    p_mem = sub.add_parser("memory", help="Manage MemoryAI context and facts")
    mem_sub = p_mem.add_subparsers(dest="memory_command", required=True)

    p_mem_list = mem_sub.add_parser("list", help="List stored memory facts")
    p_mem_list.add_argument("--tag", help="Filter by tag")
    p_mem_list.add_argument("--category", help="Filter by category")
    p_mem_list.set_defaults(func=_cmd_memory_list)

    p_mem_query = mem_sub.add_parser("query", help="Query stored memory context")
    p_mem_query.add_argument("query", help="Search query string")
    p_mem_query.add_argument("--limit", type=int, default=5, help="Maximum number of hits")
    p_mem_query.add_argument("--tag", help="Filter by tag")
    p_mem_query.add_argument("--category", help="Filter by category")
    p_mem_query.set_defaults(func=_cmd_memory_query)

    p_mem_add = mem_sub.add_parser("add", help="Add or update a memory fact")
    p_mem_add.add_argument("key", help="Fact key")
    p_mem_add.add_argument("value", help="Fact value")
    p_mem_add.add_argument("--tag", help="Comma-separated tags")
    p_mem_add.add_argument("--category", help="Fact category")
    p_mem_add.set_defaults(func=_cmd_memory_add)

    p_mem_rem = mem_sub.add_parser("remove", help="Remove a fact from memory")
    p_mem_rem.add_argument("key", help="Fact key to remove")
    p_mem_rem.set_defaults(func=_cmd_memory_remove)

    p_mem_clear = mem_sub.add_parser("clear", help="Clear all stored memory")
    p_mem_clear.set_defaults(func=_cmd_memory_clear)

    p_mem_exp = mem_sub.add_parser("export", help="Export memory snapshot to a JSON file")
    p_mem_exp.add_argument("file", help="Export file path")
    p_mem_exp.set_defaults(func=_cmd_memory_export)

    p_mem_imp = mem_sub.add_parser("import", help="Import memory snapshot from a JSON file")
    p_mem_imp.add_argument("file", help="Import file path")
    p_mem_imp.add_argument("--overwrite", action="store_true", help="Overwrite existing memory instead of merging")
    p_mem_imp.set_defaults(func=_cmd_memory_import)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    sys.exit(main())
