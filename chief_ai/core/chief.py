"""The Chief AI orchestrator.

``ChiefAI`` is the only agent the user talks to. It:

* understands a goal (``plan``),
* breaks it into tasks (via :mod:`chief_ai.core.router`),
* routes each task to the right specialist (``dispatch``),
* combines the results into one coherent response (``synthesize``).

Memory context retrieved from :class:`chief_ai.core.memory.MemoryAI` is injected
into every sub-agent prompt so specialists build on prior context. Independent
tasks can be executed in parallel with dependency-aware scheduling.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Iterator, Optional

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
            dep = f"  (depends on: {', '.join(t.dependencies)})" if t.dependencies else ""
            lines.append(f"{t.id}. [{dept}] → {agent}{dep}")
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

    # -- memory context ----------------------------------------------------
    def _memory_context(self, text: str, exclude: tuple[str, ...] = ()) -> str:
        hits = self.memory.retrieve(text, exclude=exclude)
        if not hits:
            return ""
        return "## Retrieved context from memory\n" + "\n".join(f"- {h}" for h in hits)

    # -- planning ----------------------------------------------------------
    def plan(self, goal: str) -> Plan:
        self.memory.remember("goal", goal)
        self.memory.log_event("plan", goal)
        return Plan(goal=goal, tasks=decompose(goal))

    # -- dispatch ----------------------------------------------------------
    def dispatch(self, task: Task) -> Result:
        if not task.sub_agent:
            raise ValueError("Task has no assigned sub-agent")
        agent = get_sub_agent(task.sub_agent)
        ctx = self._memory_context(task.description)
        prompt = (
            f"Goal: {task.description}\n\n"
            f"You are the {agent.name} specialist. Complete your part of this goal "
            f"and return a focused, integratable result."
        )
        if ctx:
            prompt += f"\n\n{ctx}"
        content = self.executor.run(task.sub_agent, prompt)
        self.memory.log_event(f"result:{task.id}", content)
        self.memory.log_event("dispatch", f"{task.id} -> {agent.id}")
        return Result(task_id=task.id, sub_agent=task.sub_agent, content=content)

    # -- scheduling --------------------------------------------------------
    def _schedule(self, plan: Plan) -> list[Result]:
        """Execute tasks respecting dependencies; independent tasks run in parallel."""
        by_id = {t.id: t for t in plan.tasks}
        pending = {t.id: t for t in plan.tasks}
        done: set[str] = set()
        results: dict[str, Result] = {}

        while pending:
            ready = [
                t
                for t in pending.values()
                if all(d in done for d in t.dependencies)
            ]
            if not ready:
                # No task is ready but work remains -> break cycles defensively.
                ready = list(pending.values())

            with ThreadPoolExecutor(max_workers=min(len(ready), 8)) as ex:
                futures = {ex.submit(self.dispatch, t): t.id for t in ready}
                for fut in futures:
                    res = fut.result()
                    results[res.task_id] = res
                    done.add(res.task_id)
                    pending.pop(res.task_id, None)

        # Return in original plan order for a stable, readable synthesis.
        return [results[t.id] for t in plan.tasks]

    # -- synthesize --------------------------------------------------------
    def synthesize(self, plan: Plan, results: list[Result]) -> str:
        ctx = self._memory_context(plan.goal, exclude=("result:", "goal"))
        sections = [f"# Chief AI — Integrated Result", "", f"Goal: {plan.goal}", ""]
        if ctx:
            sections.append(ctx)
            sections.append("")
        for task in plan.tasks:
            res = next((r for r in results if r.task_id == task.id), None)
            if not res:
                continue
            agent = get_sub_agent(task.sub_agent)
            sections.append(f"## {agent.name} ({agent.department})")
            sections.append(res.content)
            sections.append("")
        return "\n".join(sections)

    # -- streaming --------------------------------------------------------
    def stream(self, goal: str, parallel: bool = False) -> Iterator[dict]:
        """Yield execution events for live UIs.

        Event shapes:
          {"type": "plan", "plan": {...}}
          {"type": "task_start", "task_id", "sub_agent"}
          {"type": "task_done", "task_id", "sub_agent", "content"}
          {"type": "done", "result": "<synthesis>"}
        """
        plan = self.plan(goal)
        yield {"type": "plan", "plan": _plan_to_dict(plan)}

        results: dict[str, Result] = {}
        if parallel:
            yield from self._stream_schedule(plan, results)
        else:
            for task in plan.tasks:
                yield {"type": "task_start", "task_id": task.id, "sub_agent": task.sub_agent}
                res = self.dispatch(task)
                results[task.id] = res
                yield {
                    "type": "task_done",
                    "task_id": task.id,
                    "sub_agent": task.sub_agent,
                    "content": res.content,
                }

        yield {"type": "done", "result": self.synthesize(plan, list(results.values()))}

    def _stream_schedule(self, plan: Plan, results: dict[str, Result]) -> Iterator[dict]:
        pending = {t.id: t for t in plan.tasks}
        done: set[str] = set()
        while pending:
            ready = [t for t in pending.values() if all(d in done for d in t.dependencies)]
            if not ready:
                ready = list(pending.values())
            for t in ready:
                yield {"type": "task_start", "task_id": t.id, "sub_agent": t.sub_agent}
            with ThreadPoolExecutor(max_workers=min(len(ready), 8)) as ex:
                futures = {ex.submit(self.dispatch, t): t.id for t in ready}
                for fut in futures:
                    res = fut.result()
                    results[res.task_id] = res
                    done.add(res.task_id)
                    pending.pop(res.task_id, None)
                    yield {
                        "type": "task_done",
                        "task_id": res.task_id,
                        "sub_agent": res.sub_agent,
                        "content": res.content,
                    }

    # -- full pipeline -----------------------------------------------------
    def execute(self, goal: str, parallel: bool = False) -> str:
        plan = self.plan(goal)
        results = self._schedule(plan) if parallel else [self.dispatch(t) for t in plan.tasks]
        return self.synthesize(plan, results)


def _plan_to_dict(plan: Plan) -> dict:
    return {
        "goal": plan.goal,
        "tasks": [
            {
                "id": t.id,
                "department": t.department,
                "sub_agent": t.sub_agent,
                "name": get_sub_agent(t.sub_agent).name if t.sub_agent else "?",
                "dependencies": list(t.dependencies),
            }
            for t in plan.tasks
        ],
    }
