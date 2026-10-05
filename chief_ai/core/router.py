"""Routing and task decomposition for the Chief AI orchestrator.

``decompose`` turns a high-level goal into a list of :class:`Task` objects,
each assigned to the most suitable sub-agent. ``route`` picks the single best
sub-agent for an arbitrary piece of text.
"""

from __future__ import annotations

import re

from .registry import DEPARTMENTS, list_sub_agents
from .types import SubAgent, Task

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _tag_hits(sub: SubAgent, text: str) -> int:
    """Count how many of a sub-agent's tags appear as substrings in text."""
    lowered = text.lower()
    return sum(1 for tag in sub.tags if tag in lowered)


def _description_overlap(sub: SubAgent, tokens: set[str]) -> float:
    return len(tokens & _tokens(sub.description)) * 0.1


def route(text: str) -> SubAgent:
    """Return the single best-matching sub-agent for ``text``."""
    tokens = _tokens(text)
    scored: list[tuple[float, SubAgent]] = []
    for sub in list_sub_agents():
        score = _tag_hits(sub, text) * 2.0 + _description_overlap(sub, tokens)
        scored.append((score, sub))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored[0][1]


# High-level intents that imply a standard multi-agent workflow.
_BUILD_INTENT = ("build", "create", "develop", "make", "ship", "launch")
_PRODUCT_NOUNS = ("portfolio", "app", "site", "website", "product", "platform", "service", "tool")


def _implications(goal: str) -> list[str]:
    lowered = goal.lower()
    has_build = any(w in lowered for w in _BUILD_INTENT)
    has_product = any(w in lowered for w in _PRODUCT_NOUNS)
    if not (has_build and has_product):
        return []
    return [
        "exec-strategy",
        "design-ui",
        "eng-frontend",
        "qa-testing",
        "doc-readme",
        "devops-cloud",
        "marketing-launch",
    ]


def decompose(goal: str) -> list[Task]:
    """Break ``goal`` into routed tasks.

    Order follows the department tree so the resulting plan reads like a
    top-to-bottom workflow.
    """
    direct: dict[str, int] = {}
    for sub in list_sub_agents():
        hits = _tag_hits(sub, goal)
        if hits:
            direct[sub.id] = hits

    # Start from direct tag matches, then layer in implied agents.
    chosen: dict[str, int] = dict(direct)
    for sid in _implications(goal):
        chosen.setdefault(sid, 0)

    if not chosen:
        best = route(goal)
        return [
            Task(
                id="t1",
                description=goal,
                department=best.department,
                sub_agent=best.id,
            )
        ]

    # Preserve department / sub-agent ordering from the registry, then wire
    # dependencies so downstream work waits for its upstream inputs.
    by_sub: dict[str, Task] = {}
    idx = 1
    for dept in DEPARTMENTS:
        for sub in dept.sub_agents:
            if sub.id in chosen:
                by_sub[sub.id] = Task(
                    id=f"t{idx}",
                    description=goal,
                    department=dept.id,
                    sub_agent=sub.id,
                )
                idx += 1

    _apply_dependencies(by_sub)
    return [by_sub[s.id] for s in _ordered() if s.id in by_sub]


# Downstream agent -> agents it must wait for (only applied when present).
_DEPENDENCIES: dict[str, list[str]] = {
    "qa-testing": ["eng-frontend", "eng-backend"],
    "doc-readme": ["eng-frontend"],
    "devops-cloud": ["eng-backend", "eng-frontend"],
    "marketing-launch": ["doc-readme", "devops-cloud"],
}


def _ordered() -> list:
    """Registry-ordered sub-agents (department then agent order)."""
    return [sub for dept in DEPARTMENTS for sub in dept.sub_agents]


def has_cycle(tasks: list[Task]) -> bool:
    """Return True if task dependencies contain a cycle."""
    id_map: dict[str, Task] = {}
    for t in tasks:
        id_map[t.id] = t
        if t.sub_agent:
            id_map[t.sub_agent] = t

    state: dict[str, int] = {t.id: 0 for t in tasks}

    def dfs(t: Task) -> bool:
        state[t.id] = 1
        for dep_id in t.dependencies:
            dep_task = id_map.get(dep_id)
            if dep_task is None:
                continue
            if state.get(dep_task.id) == 1:
                return True
            if state.get(dep_task.id) == 0:
                if dfs(dep_task):
                    return True
        state[t.id] = 2
        return False

    for t in tasks:
        if state[t.id] == 0:
            if dfs(t):
                return True
    return False


def topological_sort(tasks: list[Task]) -> list[Task]:
    """Return tasks in topological order based on dependencies.

    If a cycle exists, returns remaining tasks in original input order.
    """
    if not tasks:
        return []

    task_by_id: dict[str, Task] = {t.id: t for t in tasks}
    id_map: dict[str, Task] = {}
    for t in tasks:
        id_map[t.id] = t
        if t.sub_agent:
            id_map[t.sub_agent] = t

    in_degree: dict[str, int] = {t.id: 0 for t in tasks}
    dependents: dict[str, list[str]] = {t.id: [] for t in tasks}

    for t in tasks:
        for dep_id in t.dependencies:
            dep_task = id_map.get(dep_id)
            if dep_task and dep_task.id in in_degree:
                in_degree[t.id] += 1
                dependents[dep_task.id].append(t.id)

    queue = [t.id for t in tasks if in_degree[t.id] == 0]
    sorted_ids: list[str] = []

    while queue:
        curr_id = queue.pop(0)
        sorted_ids.append(curr_id)
        for dep_id in dependents[curr_id]:
            in_degree[dep_id] -= 1
            if in_degree[dep_id] == 0:
                queue.append(dep_id)

    if len(sorted_ids) < len(tasks):
        remaining = [t.id for t in tasks if t.id not in sorted_ids]
        sorted_ids.extend(remaining)

    return [task_by_id[tid] for tid in sorted_ids]


def _apply_dependencies(by_sub: dict[str, Task]) -> None:
    for sub_id, upstream in _DEPENDENCIES.items():
        if sub_id in by_sub:
            task = by_sub[sub_id]
            for u in upstream:
                if u in by_sub:
                    task.dependencies.append(u)
                    if has_cycle(list(by_sub.values())):
                        task.dependencies.pop()
