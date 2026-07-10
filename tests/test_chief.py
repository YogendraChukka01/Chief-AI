import os
import tempfile

import yaml

from chief_ai.core.chief import ChiefAI, Executor, MockExecutor
from chief_ai.core.registry import get_sub_agent
from chief_ai.core.router import decompose
from chief_ai.integrations.opencode_generator import generate


class CapturingExecutor(Executor):
    def __init__(self):
        self.last_prompt = ""

    def run(self, sub_agent_id: str, prompt: str) -> str:
        self.last_prompt = prompt
        return f"[{get_sub_agent(sub_agent_id).name}] done"


def test_memory_context_injected_into_prompt():
    from chief_ai.core.memory import MemoryAI

    mem = MemoryAI(path=".chief_memory/_test_memory.json")
    mem.remember("portfolio", "v1 was built with React and Tailwind")
    chief = ChiefAI(memory=mem, executor=CapturingExecutor())
    plan = chief.plan("Build the next version of my portfolio")
    chief.dispatch(plan.tasks[0])
    assert "Retrieved context from memory" in chief.executor.last_prompt
    assert "React" in chief.executor.last_prompt


def test_decompose_sets_dependency_dag():
    tasks = {t.sub_agent: t for t in decompose("Build the next version of my portfolio")}
    assert "eng-frontend" in tasks["qa-testing"].dependencies
    assert tasks["doc-readme"].dependencies == ["eng-frontend"]
    assert set(tasks["marketing-launch"].dependencies) == {"doc-readme", "devops-cloud"}


def test_parallel_execution_returns_all_sections():
    chief = ChiefAI(executor=MockExecutor())
    out = chief.execute("Build the next version of my portfolio", parallel=True)
    for agent in ("Strategy", "Frontend Expert", "UI Designer", "Testing", "READMEs", "Launch Strategy"):
        assert agent in out


def test_default_model_emitted_when_env_set():
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


def test_results_not_leaked_into_synthesis():
    chief = ChiefAI(executor=MockExecutor())
    out = chief.execute("Build a mobile app")
    # Per-task results must appear as structured sections, not as raw
    # "result:t3: ..." memory noise at the top of the synthesis.
    assert "result:t" not in out
    # But the structured sections must still be present.
    assert "Mobile Expert" in out
