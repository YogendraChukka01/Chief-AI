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


def test_scheduling_handles_cyclic_dependencies_defensively() -> None:
    from chief_ai.core.chief import Plan
    from chief_ai.core.types import Task

    executor = CapturingExecutor()
    chief = ChiefAI(executor=executor)
    # Construct a plan with artificial cycle
    tasks = [
        Task(id="t1", description="Task 1", sub_agent="eng-frontend", dependencies=["eng-backend"]),
        Task(id="t2", description="Task 2", sub_agent="eng-backend", dependencies=["eng-frontend"]),
    ]
    plan = Plan(goal="Test cycle", tasks=tasks)
    results = chief._schedule(plan)
    assert len(results) == 2
    assert set(executor.dispatched_order) == {"eng-frontend", "eng-backend"}
