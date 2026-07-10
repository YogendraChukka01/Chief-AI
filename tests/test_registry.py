from chief_ai.core.registry import DEPARTMENTS, get_sub_agent, list_sub_agents
from chief_ai.core.types import Permission

EXPECTED_DEPTS = {
    "executive",
    "engineering",
    "design",
    "devops",
    "qa",
    "documentation",
    "research",
    "marketing",
    "finance",
    "legal",
    "memory",
}


def test_eleven_departments():
    ids = {d.id for d in DEPARTMENTS}
    assert ids == EXPECTED_DEPTS


def test_sub_agent_count_and_unique_ids():
    subs = list_sub_agents()
    ids = [s.id for s in subs]
    assert len(ids) == len(set(ids)), "sub-agent ids must be unique"
    assert len(subs) >= 50


def test_every_sub_agent_has_permissions_and_prompt():
    for s in list_sub_agents():
        assert set(s.permissions.keys()) == set(Permission), s.id
        assert s.prompt.strip()


def test_get_sub_agent_lookup():
    assert get_sub_agent("eng-frontend").name == "Frontend Expert"
