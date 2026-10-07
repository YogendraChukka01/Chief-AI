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


def test_topological_sort_and_cycle_detection() -> None:
    from chief_ai.core.router import topological_sort
    from chief_ai.core.types import Task

    # A -> B -> C
    t1 = Task(id="t1", description="Task 1", sub_agent="agent1", dependencies=[])
    t2 = Task(id="t2", description="Task 2", sub_agent="agent2", dependencies=["agent1"])
    t3 = Task(id="t3", description="Task 3", sub_agent="agent3", dependencies=["agent2"])

    sorted_tasks = topological_sort([t3, t2, t1])
    ids = [t.id for t in sorted_tasks]
    assert ids == ["t1", "t2", "t3"]

    # Cyclic dependency: t1 depends on t2, t2 depends on t1
    c1 = Task(id="c1", description="Cycle 1", sub_agent="c_agent1", dependencies=["c_agent2"])
    c2 = Task(id="c2", description="Cycle 2", sub_agent="c_agent2", dependencies=["c_agent1"])

    cycle_sorted = topological_sort([c1, c2])
    assert len(cycle_sorted) == 2
    assert {t.id for t in cycle_sorted} == {"c1", "c2"}
