from chief_ai.core.router import decompose, route

BUILD_GOAL = "Build the next version of my portfolio."


def test_route_picks_testing_agent() -> None:
    assert route("write unit tests for the parser").id == "qa-testing"


def test_route_picks_readme_agent() -> None:
    assert route("update the README with setup steps").id == "doc-readme"


def test_decompose_implies_workflow_for_build_goal() -> None:
    tasks = decompose(BUILD_GOAL)
    ids = {t.sub_agent for t in tasks}
    # A "build ... portfolio" goal should pull in the standard product workflow.
    assert "exec-strategy" in ids
    assert "design-ui" in ids
    assert "eng-frontend" in ids
    assert "qa-testing" in ids
    assert "doc-readme" in ids
    assert "devops-cloud" in ids
    assert "marketing-launch" in ids


def test_decompose_orders_by_department() -> None:
    tasks = decompose(BUILD_GOAL)
    positions = {t.sub_agent: i for i, t in enumerate(tasks)}
    # Executive should come before Engineering, which comes before Marketing.
    assert positions["exec-strategy"] < positions["eng-frontend"] < positions["marketing-launch"]


def test_decompose_fallback_single_task() -> None:
    tasks = decompose("zzz qqq weird unknown intent")
    assert len(tasks) == 1


def test_has_cycle_detection() -> None:
    from chief_ai.core.router import has_cycle
    from chief_ai.core.types import Task

    t1 = Task(id="t1", description="t1", sub_agent="a1", dependencies=["a2"])
    t2 = Task(id="t2", description="t2", sub_agent="a2", dependencies=["a1"])
    assert has_cycle([t1, t2]) is True

    t3 = Task(id="t3", description="t3", sub_agent="a3", dependencies=[])
    t4 = Task(id="t4", description="t4", sub_agent="a4", dependencies=["a3"])
    assert has_cycle([t3, t4]) is False


def test_topological_sort() -> None:
    from chief_ai.core.router import topological_sort
    from chief_ai.core.types import Task

    t1 = Task(id="t1", description="t1", sub_agent="a1", dependencies=["a2"])
    t2 = Task(id="t2", description="t2", sub_agent="a2", dependencies=[])
    t3 = Task(id="t3", description="t3", sub_agent="a3", dependencies=["a1"])

    ordered = topological_sort([t1, t3, t2])
    order_ids = [t.sub_agent for t in ordered]
    assert order_ids.index("a2") < order_ids.index("a1")
    assert order_ids.index("a1") < order_ids.index("a3")
