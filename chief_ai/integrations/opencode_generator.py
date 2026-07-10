"""Generate opencode-native agent definitions from the Chief AI registry.

Running :func:`generate` writes one Markdown file per sub-agent into
``.opencode/agents/`` plus a ``chief`` primary agent and a root ``opencode.json``.
The generated files are the live execution layer: the Chief AI (``chief.md``)
delegates real work to the specialists via opencode's Task tool / @mentions.
"""

from __future__ import annotations

import os
from typing import Optional

import yaml

from ..config import default_model
from ..core.registry import DEPARTMENTS, list_sub_agents
from ..core.types import Permission, SubAgent

AGENTS_DIR = os.path.join(".opencode", "agents")


def _frontmatter(block: dict) -> str:
    return "---\n" + yaml.safe_dump(block, default_flow_style=False, sort_keys=False) + "---\n"


def render_subagent(sub: SubAgent) -> str:
    perms = sub.permission_map()
    block = {
        "name": sub.id,
        "mode": "subagent",
        "description": sub.description,
        "permissions": perms,
    }
    model = sub.model or default_model()
    if model:
        block["model"] = model
    return _frontmatter(block) + "\n" + sub.prompt + "\n"


def render_chief() -> str:
    dept_lines = []
    for d in DEPARTMENTS:
        members = ", ".join(f"@{s.id}" for s in d.sub_agents)
        dept_lines.append(f"- **{d.name}**: {members}")
    departments = "\n".join(dept_lines)

    prompt = f"""You are the **Chief AI**, the single orchestrator the user talks to.
You manage a team of specialized sub-agents across these departments:

{departments}

## How you operate
1. Understand the user's goal.
2. Decompose it into tasks and decide which specialist(s) should handle each.
3. Delegate with the Task tool or by @mentioning the sub-agent, e.g. `@eng-frontend`.
4. Combine the returned results into ONE coherent response for the user.
5. Track progress and keep the user's original intent in focus.

Stay at the orchestration level. Do the specialist work through your sub-agents,
never by impersonating them. When tasks depend on each other, sequence them.
"""

    block = {
        "name": "chief",
        "mode": "primary",
        "description": "Chief AI orchestrator: decomposes goals and delegates to specialist sub-agents.",
        "permissions": {
            "read": True,
            "write": True,
            "execute": True,
            "network": True,
            "task": {"*": "allow"},
        },
    }
    return _frontmatter(block) + "\n" + prompt + "\n"


def render_opencode_json() -> str:
    block = {
        "$schema": "https://opencode.ai/config.json",
        "agent": {"chief": {"mode": "primary"}},
    }
    return yaml.safe_dump(block, default_flow_style=False, sort_keys=False)


def _write_opencode_json(target_dir: str) -> str:
    """Write opencode.json, merging the chief entry into any existing config.

    This avoids clobbering a user's providers, models, or other settings.
    """
    path = os.path.join(target_dir, "opencode.json")
    data: dict = {
        "$schema": "https://opencode.ai/config.json",
        "agent": {"chief": {"mode": "primary"}},
    }
    if os.path.exists(path):
        try:
            with open(path, encoding="utf-8") as fh:
                existing = yaml.safe_load(fh) or {}
            if isinstance(existing, dict):
                existing.setdefault("$schema", data["$schema"])
                existing.setdefault("agent", {})
                existing["agent"]["chief"] = {"mode": "primary"}
                data = existing
        except (OSError, yaml.YAMLError):
            pass
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(yaml.safe_dump(data, default_flow_style=False, sort_keys=False))
    return path


def generate(target_dir: str = ".") -> list[str]:
    """Write all agent files. Returns the list of written paths."""
    agents_path = os.path.join(target_dir, AGENTS_DIR)
    os.makedirs(agents_path, exist_ok=True)

    written: list[str] = []

    chief_path = os.path.join(agents_path, "chief.md")
    with open(chief_path, "w", encoding="utf-8") as fh:
        fh.write(render_chief())
    written.append(chief_path)

    for sub in list_sub_agents():
        path = os.path.join(agents_path, f"{sub.id}.md")
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(render_subagent(sub))
        written.append(path)

    cfg_path = _write_opencode_json(target_dir)
    written.append(cfg_path)

    return written
