"""The Chief AI orchestrator.

``ChiefAI`` is the only agent the user talks to. It:

* understands a goal (``plan``),
* breaks it into tasks (via :mod:`chief_ai.core.router`),
* routes each task to the right specialist (``dispatch``),
* combines the results into one coherent response (``synthesize``).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional

from .memory import MemoryAI
from .registry import get_department, get_sub_agent
from .router import decompose
from .types import Result, Task


@dataclass
class Plan:
    goal: str
    tasks: list[Task]

    def render(self) -> str:
        lines = [f"# Chief AI Plan", "", f"Goal: {self.goal}", "", "## Tasks", ""]
        for t in self.tasks:
            dept = get_department(t.department).name if t.department else "?"
            agent = get_sub_agent(t.sub_agent).name if t.sub_agent else "?"
            lines.append(f"{t.id}. [{dept}] → {agent}")
        return "\n".join(lines)


class Executor(ABC):
    """Runs a single sub-agent task and returns its output."""

    @abstractmethod
    def run(self, sub_agent_id: str, prompt: str) -> str:
        ...


class MockExecutor(Executor):
    """Returns a deterministic placeholder instead of calling a real LLM.

    Useful for testing the orchestration and for previewing a plan.
    """

    def run(self, sub_agent_id: str, prompt: str) -> str:
        agent = get_sub_agent(sub_agent_id)
        return (
            f"[{agent.name}] acknowledged task.\n"
            f"Department: {agent.department}\n"
            f"Focus: {', '.join(agent.tags[:3])}…\n"
            f"(MockExecutor: no LLM call made.)"
        )


class ChiefAI:
    def __init__(self, memory: Optional[MemoryAI] = None, executor: Optional[Executor] = None) -> None:
        self.memory = memory or MemoryAI()
        self.executor = executor or MockExecutor()

    # -- planning ----------------------------------------------------------
    def plan(self, goal: str) -> Plan:
        self.memory.remember("goal", goal)
        return Plan(goal=goal, tasks=decompose(goal))

    # -- dispatch ----------------------------------------------------------
    def dispatch(self, task: Task) -> Result:
        if not task.sub_agent:
            raise ValueError("Task has no assigned sub-agent")
        agent = get_sub_agent(task.sub_agent)
        prompt = (
            f"Goal: {task.description}\n\n"
            f"You are the {agent.name} specialist. Complete your part of this goal "
            f"and return a focused, integratable result."
        )
        content = self.executor.run(task.sub_agent, prompt)
        self.memory.remember(f"result:{task.id}", content)
        return Result(task_id=task.id, sub_agent=task.sub_agent, content=content)

    # -- synthesize --------------------------------------------------------
    def synthesize(self, plan: Plan, results: list[Result]) -> str:
        by_id = {r.task_id: r for r in results}
        sections = [f"# Chief AI — Integrated Result", "", f"Goal: {plan.goal}", ""]
        for task in plan.tasks:
            res = by_id.get(task.id)
            if not res:
                continue
            agent = get_sub_agent(task.sub_agent)
            sections.append(f"## {agent.name} ({agent.department})")
            sections.append(res.content)
            sections.append("")
        return "\n".join(sections)

    # -- full pipeline -----------------------------------------------------
    def execute(self, goal: str) -> str:
        plan = self.plan(goal)
        results = [self.dispatch(t) for t in plan.tasks]
        return self.synthesize(plan, results)
