from chief_ai.core.router import decompose, route

BUILD_GOAL = "Build the next version of my portfolio."


def test_route_picks_testing_agent():
    assert route("write unit tests for the parser").id == "qa-testing"


def test_route_picks_readme_agent():
    assert route("update the README with setup steps").id == "doc-readme"


def test_decompose_implies_workflow_for_build_goal():
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


def test_decompose_orders_by_department():
    tasks = decompose(BUILD_GOAL)
    positions = {t.sub_agent: i for i, t in enumerate(tasks)}
    # Executive should come before Engineering, which comes before Marketing.
    assert positions["exec-strategy"] < positions["eng-frontend"] < positions["marketing-launch"]


def test_decompose_fallback_single_task():
    tasks = decompose("zzz qqq weird unknown intent")
    assert len(tasks) == 1
