import os
import tempfile

import yaml

from chief_ai.core.chief import ChiefAI, Executor, MockExecutor
from chief_ai.core.registry import get_sub_agent
from chief_ai.core.router import decompose
from chief_ai.integrations.opencode_generator import generate


class CapturingExecutor(Executor):
    def __init__(self) -> None:
        self.last_prompt = ""
        self.dispatched_order: list[str] = []

    def run(self, sub_agent_id: str, prompt: str) -> str:
        self.last_prompt = prompt
        self.dispatched_order.append(sub_agent_id)
        return f"[{get_sub_agent(sub_agent_id).name}] done"


def test_memory_context_injected_into_prompt() -> None:
    from chief_ai.core.memory import MemoryAI

    mem = MemoryAI(path=".chief_memory/_test_memory.json")
    mem.remember("portfolio", "v1 was built with React and Tailwind")
    chief = ChiefAI(memory=mem, executor=CapturingExecutor())
    plan = chief.plan("Build the next version of my portfolio")
    chief.dispatch(plan.tasks[0])
    assert isinstance(chief.executor, CapturingExecutor)
    assert "Retrieved context from memory" in chief.executor.last_prompt
    assert "React" in chief.executor.last_prompt


def test_decompose_sets_dependency_dag() -> None:
    tasks = {t.sub_agent: t for t in decompose("Build the next version of my portfolio")}
    assert "eng-frontend" in tasks["qa-testing"].dependencies
    assert tasks["doc-readme"].dependencies == ["eng-frontend"]
    assert set(tasks["marketing-launch"].dependencies) == {"doc-readme", "devops-cloud"}


def test_parallel_execution_returns_all_sections() -> None:
    chief = ChiefAI(executor=MockExecutor())
    out = chief.execute("Build the next version of my portfolio", parallel=True)
    for agent in (
        "Strategy",
        "Frontend Expert",
        "UI Designer",
        "Testing",
        "READMEs",
        "Launch Strategy",
    ):
        assert agent in out


def test_parallel_scheduling_respects_dependency_order() -> None:
    executor = CapturingExecutor()
    chief = ChiefAI(executor=executor)
    chief.execute("Build the next version of my portfolio", parallel=True)
    order = executor.dispatched_order
    # eng-frontend must be dispatched before qa-testing and doc-readme
    assert "eng-frontend" in order
    assert "qa-testing" in order
    assert "doc-readme" in order
    assert order.index("eng-frontend") < order.index("qa-testing")
    assert order.index("eng-frontend") < order.index("doc-readme")


def test_default_model_emitted_when_env_set() -> None:
    os.environ["CHIEF_MODEL"] = "anthropic/test-model"
    try:
        with tempfile.TemporaryDirectory() as tmp:
            generate(tmp)
            path = os.path.join(tmp, ".opencode", "agents", "eng-frontend.md")
            with open(path) as fh:
                fm = yaml.safe_load(fh.read().split("---\n", 2)[1])
            assert fm["model"] == "anthropic/test-model"
    finally:
        del os.environ["CHIEF_MODEL"]


def test_results_not_leaked_into_synthesis() -> None:
    chief = ChiefAI(executor=MockExecutor())
    out = chief.execute("Build a mobile app")
    # Per-task results must appear as structured sections, not as raw
    # "result:t3: ..." memory noise at the top of the synthesis.
    assert "result:t" not in out
    # But the structured sections must still be present.
    assert "Mobile Expert" in out


def test_dispatch_injects_upstream_results() -> None:
    executor = CapturingExecutor()
    chief = ChiefAI(executor=executor)
    # Execute through pipeline so upstream results build up
    chief.execute("Build the next version of my portfolio")
    # Check that qa-testing received upstream outputs from eng-frontend
    last_prompt = executor.last_prompt
    assert "Upstream Task Outputs" in last_prompt or "Frontend Expert" in last_prompt


def test_result_status_tracking() -> None:
    from chief_ai.core.types import TaskStatus

    class FailingExecutor(Executor):
        def run(self, sub_agent_id: str, prompt: str) -> str:
            raise RuntimeError("LLM connection failed")

    chief = ChiefAI(executor=FailingExecutor())
    plan = chief.plan("Fix a bug in backend")
    res = chief.dispatch(plan.tasks[0])
    assert res.status == TaskStatus.FAILED
    assert "Error executing task" in res.content
    assert "LLM connection failed" in res.content


def test_dispatch_retry_on_failure() -> None:
    from chief_ai.core.types import Task, TaskStatus

    class FlakyExecutor(Executor):
        def __init__(self) -> None:
            self.calls = 0

        def run(self, sub_agent_id: str, prompt: str) -> str:
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("Transient network issue")
            return "Success on retry"

    chief = ChiefAI(executor=FlakyExecutor(), max_retries=2)
    task = Task(id="t1", description="Test task", sub_agent="eng-backend")
    res = chief.dispatch(task)

    assert res.status == TaskStatus.SUCCESS
    assert res.content == "Success on retry"
    assert res.metadata.get("attempts") == "2"


def test_dispatch_max_retries_exceeded() -> None:
    from chief_ai.core.types import Task, TaskStatus

    class AlwaysFailingExecutor(Executor):
        def run(self, sub_agent_id: str, prompt: str) -> str:
            raise RuntimeError("Persistent error")

    chief = ChiefAI(executor=AlwaysFailingExecutor(), max_retries=2)
    task = Task(id="t1", description="Test task", sub_agent="eng-backend")
    res = chief.dispatch(task)

    assert res.status == TaskStatus.FAILED
    assert "Persistent error" in res.content
    assert res.metadata.get("attempts") == "3"


def test_retry_prompt_feedback_injection() -> None:
    from chief_ai.core.types import Task

    prompts: list[str] = []

    class CapturingFlakyExecutor(Executor):
        def __init__(self) -> None:
            self.calls = 0

        def run(self, sub_agent_id: str, prompt: str) -> str:
            prompts.append(prompt)
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("Syntax error in generated code")
            return "Fixed code output"

    chief = ChiefAI(executor=CapturingFlakyExecutor(), max_retries=1)
    task = Task(id="t1", description="Write function", sub_agent="eng-backend")
    chief.dispatch(task)

    assert len(prompts) == 2
    assert "Previous Attempt Failure" in prompts[1]
    assert "Syntax error in generated code" in prompts[1]
