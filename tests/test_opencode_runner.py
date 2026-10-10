"""Tests for OpencodeRunner and AsyncOpencodeRunner adapters."""

from __future__ import annotations

import pytest

from chief_ai.integrations.opencode_runner import AsyncOpencodeRunner, OpencodeRunner


def test_opencode_runner_missing_binary(monkeypatch) -> None:
    monkeypatch.setattr("shutil.which", lambda bin_name: None)
    runner = OpencodeRunner(binary="nonexistent_opencode_cmd")
    with pytest.raises(RuntimeError, match="binary not found on PATH"):
        runner.run("eng-frontend", "build app")


@pytest.mark.asyncio
async def test_async_opencode_runner_missing_binary(monkeypatch) -> None:
    monkeypatch.setattr("shutil.which", lambda bin_name: None)
    runner = AsyncOpencodeRunner(binary="nonexistent_opencode_cmd")
    with pytest.raises(RuntimeError, match="binary not found on PATH"):
        await runner.run_async("eng-frontend", "build app")
