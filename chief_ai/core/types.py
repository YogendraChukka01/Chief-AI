"""Core data types for the Chief AI agent system."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class Permission(str, Enum):
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
    model: Optional[str] = None
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
    department: Optional[str] = None
    sub_agent: Optional[str] = None
    dependencies: list[str] = field(default_factory=list)


@dataclass
class Result:
    """The output produced by a sub-agent for a task."""

    task_id: str
    sub_agent: str
    content: str
