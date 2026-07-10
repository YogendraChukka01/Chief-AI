"""Command-line interface for the Chief AI system.

Usage:
    chief plan "build the next version of my portfolio"
    chief run  "build the next version of my portfolio" [--opencode]
    chief generate [--target .]
    chief list
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Optional

from .core.chief import ChiefAI, MockExecutor
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

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
