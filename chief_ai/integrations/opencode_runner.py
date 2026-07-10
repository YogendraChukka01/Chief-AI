"""Headless execution of sub-agents through the opencode CLI.

This adapter lets :class:`chief_ai.core.chief.ChiefAI` run each task as a real
opencode sub-agent instead of the :class:`MockExecutor`. It shells out to the
``opencode`` binary (``opencode run "@<agent> <prompt>"``). If the binary is not
installed, :meth:`OpencodeRunner.run` raises a clear error.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Optional

from ..core.chief import Executor
from ..core.registry import get_sub_agent


class OpencodeRunner(Executor):
    def __init__(self, timeout: int = 600, binary: str = "opencode") -> None:
        self.timeout = timeout
        self.binary = binary

    def _ensure_binary(self) -> None:
        if shutil.which(self.binary) is None:
            raise RuntimeError(
                f"`{self.binary}` binary not found on PATH. Install opencode "
                "(https://opencode.ai) or use MockExecutor for preview."
            )

    def run(self, sub_agent_id: str, prompt: str) -> str:
        self._ensure_binary()
        agent = get_sub_agent(sub_agent_id)
        message = f"@{agent.id} {prompt}"
        proc = subprocess.run(
            [self.binary, "run", message],
            capture_output=True,
            text=True,
            timeout=self.timeout,
        )
        if proc.returncode != 0:
            return f"[{agent.name}] execution failed (exit {proc.returncode}):\n{proc.stderr}"
        return proc.stdout.strip() or f"[{agent.name}] returned no output."
