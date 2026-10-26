"""Core data types for the Chief AI agent system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class Permission(StrEnum):
    """Filesystem / runtime permission tiers used for opencode agent generation."""

    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    NETWORK = "network"


# Tools the Python orchestrator is aware of. These map onto opencode
# permissions when the registry is compiled into .opencode/ agent files.
TOOL_PERMISSION: dict[str, Permission] = {
    "read": Permission.READ,
    "write": Permission.WRITE,
    "bash": Permission.EXECUTE,
    "web": Permission.NETWORK,
}


@dataclass
class SubAgent:
    """A single specialist agent belonging to a department."""

    id: str
    name: str
    department: str
    description: str
    tags: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    permissions: dict[Permission, bool] = field(default_factory=dict)
    model: str | None = None
    prompt: str = ""

    def permission_map(self) -> dict[str, bool]:
        """Flatten permissions into opencode-style string keys."""
        return {p.value: v for p, v in self.permissions.items()}


@dataclass
class Department:
    """A group of related sub-agents under one executive function."""

    id: str
    name: str
    description: str
    sub_agents: list[SubAgent] = field(default_factory=list)


@dataclass
class Task:
    """A unit of work routed to a sub-agent, optionally depending on others."""

    id: str
    description: str
    department: str | None = None
    sub_agent: str | None = None
    dependencies: list[str] = field(default_factory=list)


class TaskStatus(StrEnum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


@dataclass
class Result:
    """The output produced by a sub-agent for a task."""

    task_id: str
    sub_agent: str
    content: str
    status: TaskStatus = TaskStatus.SUCCESS
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class ExecutionSummary:
    """Execution metrics and aggregated task results."""

    goal: str
    duration_seconds: float
    total_tasks: int
    succeeded_tasks: int
    failed_tasks: int
    total_attempts: int
    results: list[Result] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "duration_seconds": round(self.duration_seconds, 3),
            "total_tasks": self.total_tasks,
            "succeeded_tasks": self.succeeded_tasks,
            "failed_tasks": self.failed_tasks,
            "total_attempts": self.total_attempts,
            "results": [
                {
                    "task_id": r.task_id,
                    "sub_agent": r.sub_agent,
                    "status": str(r.status),
                    "attempts": int(r.metadata.get("attempts", "1")),
                    "content": r.content,
                }
                for r in self.results
            ],
        }

    def to_json(self) -> str:
        import json

        return json.dumps(self.to_dict(), indent=2)

    def to_markdown(self) -> str:
        lines = [
            "# Chief AI Execution Summary",
            "",
            f"- **Goal**: {self.goal}",
            f"- **Duration**: {self.duration_seconds:.2f}s",
            f"- **Total Tasks**: {self.total_tasks}",
            f"- **Succeeded**: {self.succeeded_tasks}",
            f"- **Failed**: {self.failed_tasks}",
            f"- **Total Attempts**: {self.total_attempts}",
            "",
            "## Task Details",
            "",
        ]
        for r in self.results:
            attempts = r.metadata.get("attempts", "1")
            status_icon = "✅" if r.status == TaskStatus.SUCCESS else "❌"
            lines.append(f"### {status_icon} Task `{r.task_id}` (@{r.sub_agent})")
            lines.append(f"- Status: **{r.status}**")
            lines.append(f"- Attempts: {attempts}")
            lines.append("")
            lines.append("```")
            lines.append(r.content)
            lines.append("```")
            lines.append("")
        return "\n".join(lines)
