"""Headless execution of sub-agents through the opencode CLI.

This adapter lets :class:`chief_ai.core.chief.ChiefAI` run each task as a real
opencode sub-agent instead of the :class:`MockExecutor`. It shells out to the
``opencode`` binary (``opencode run "@<agent> <prompt>"``). If the binary is not
installed, :meth:`OpencodeRunner.run` raises a clear error.
"""

from __future__ import annotations

import asyncio
import shutil
import subprocess

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

    async def run_async(self, sub_agent_id: str, prompt: str) -> str:
        self._ensure_binary()
        agent = get_sub_agent(sub_agent_id)
        message = f"@{agent.id} {prompt}"
        try:
            proc = await asyncio.create_subprocess_exec(
                self.binary,
                "run",
                message,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=self.timeout)
            out_str = stdout.decode("utf-8", errors="replace").strip()
            err_str = stderr.decode("utf-8", errors="replace").strip()
            if proc.returncode != 0:
                return f"[{agent.name}] execution failed (exit {proc.returncode}):\n{err_str}"
            return out_str or f"[{agent.name}] returned no output."
        except TimeoutError:
            return f"[{agent.name}] execution timed out after {self.timeout}s."
