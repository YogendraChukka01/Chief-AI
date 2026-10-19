from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from chief_ai.cli import build_parser
from chief_ai.core.chief import ChiefAI, Executor
from chief_ai.core.types import TaskStatus
from chief_ai.integrations.opencode_runner import ExecutionError, OpencodeRunner


class FlakyExecutor(Executor):
    def __init__(self, fail_count: int = 1) -> None:
        self.fail_count = fail_count
        self.calls = 0
        self.prompts: list[str] = []

    def run(self, sub_agent_id: str, prompt: str) -> str:
        self.calls += 1
        self.prompts.append(prompt)
        if self.calls <= self.fail_count:
            raise RuntimeError(f"Simulated failure attempt {self.calls}")
        return f"Success on attempt {self.calls}"


def test_retry_success_after_failure(tmp_path) -> None:
    from chief_ai.core.memory import MemoryAI

    mem = MemoryAI(path=str(tmp_path / "mem.json"))
    executor = FlakyExecutor(fail_count=1)
    chief = ChiefAI(memory=mem, executor=executor, max_retries=2)
    plan = chief.plan("Fix a bug in backend")

    res = chief.dispatch(plan.tasks[0])

    assert res.status == TaskStatus.SUCCESS
    assert executor.calls == 2
    assert "Success on attempt 2" in res.content
    assert res.metadata["attempts"] == "2"
    assert res.metadata["retries"] == "1"

    # Verify second prompt included execution error feedback
    second_prompt = executor.prompts[1]
    assert "Execution Error Feedback" in second_prompt
    assert "Simulated failure attempt 1" in second_prompt

    # Verify retry event logged in memory
    events = [h for h in chief.memory.history() if h.get("event", "").startswith("retry:")]
    assert len(events) == 1
    assert "Attempt 1 failed" in events[0]["detail"]


def test_retry_exhaustion_failure(tmp_path) -> None:
    from chief_ai.core.memory import MemoryAI

    mem = MemoryAI(path=str(tmp_path / "mem.json"))
    executor = FlakyExecutor(fail_count=5)
    chief = ChiefAI(memory=mem, executor=executor, max_retries=2)
    plan = chief.plan("Fix a bug in backend")

    res = chief.dispatch(plan.tasks[0])

    assert res.status == TaskStatus.FAILED
    assert executor.calls == 3
    assert "Error executing task" in res.content
    assert res.metadata["attempts"] == "3"
    assert res.metadata["retries"] == "2"


def test_opencode_runner_raises_execution_error() -> None:
    runner = OpencodeRunner(binary="opencode")
    mock_completed_process = subprocess.CompletedProcess(
        args=["opencode", "run", "test"],
        returncode=1,
        stdout="",
        stderr="opencode error occurred",
    )

    with (
        patch("shutil.which", return_value="/usr/bin/opencode"),
        patch("subprocess.run", return_value=mock_completed_process),
        pytest.raises(ExecutionError, match="execution failed \\(exit 1\\)"),
    ):
        runner.run("eng-backend", "Do backend work")


def test_cli_max_retries_parsing() -> None:
    parser = build_parser()

    args_run = parser.parse_args(["run", "Build portfolio", "--max-retries", "3"])
    assert args_run.max_retries == 3

    args_serve = parser.parse_args(["serve", "--max-retries", "2"])
    assert args_serve.max_retries == 2
