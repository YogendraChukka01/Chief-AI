import os
import tempfile

import yaml

from chief_ai.core.registry import list_sub_agents
from chief_ai.integrations.opencode_generator import generate


def _load_frontmatter(text: str) -> dict:
    assert text.startswith("---\n")
    body = text.split("---\n", 2)[1]
    return yaml.safe_load(body)


def test_generate_writes_chief_and_all_subagents():
    with tempfile.TemporaryDirectory() as tmp:
        written = generate(tmp)
        names = {os.path.basename(p) for p in written}
        assert "chief.md" in names
        assert "opencode.json" in names
        for sub in list_sub_agents():
            assert f"{sub.id}.md" in names


def test_generated_subagent_frontmatter_is_valid():
    with tempfile.TemporaryDirectory() as tmp:
        generate(tmp)
        path = os.path.join(tmp, ".opencode", "agents", "eng-frontend.md")
        with open(path) as fh:
            fm = _load_frontmatter(fh.read())
        assert fm["name"] == "eng-frontend"
        assert fm["mode"] == "subagent"
        assert fm["permissions"]["write"] is True


def test_generated_chief_is_primary_with_task_access():
    with tempfile.TemporaryDirectory() as tmp:
        generate(tmp)
        path = os.path.join(tmp, ".opencode", "agents", "chief.md")
        with open(path) as fh:
            fm = _load_frontmatter(fh.read())
        assert fm["mode"] == "primary"
        assert fm["permissions"]["task"]["*"] == "allow"
