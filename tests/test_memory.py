import json
import os
import tempfile
from chief_ai.cli import main
from chief_ai.core.memory import MemoryAI


def test_memory_remember_recall_forget(tmp_path):
    mem_file = os.path.join(tmp_path, "memory.json")
    mem = MemoryAI(path=mem_file)

    mem.remember("framework", "pydantic-ai", tags=["ai", "python"], category="tech")
    assert mem.recall("framework") == "pydantic-ai"
    assert mem.get_fact_meta("framework") == {"tags": ["ai", "python"], "category": "tech"}

    facts = mem.list_facts(tag="ai")
    assert "framework" in facts

    facts_cat = mem.list_facts(category="tech")
    assert "framework" in facts_cat

    facts_other = mem.list_facts(category="other")
    assert "framework" not in facts_other

    assert mem.forget("framework") is True
    assert mem.recall("framework") is None
    assert mem.forget("nonexistent") is False


def test_memory_clear_and_history(tmp_path):
    mem_file = os.path.join(tmp_path, "memory.json")
    mem = MemoryAI(path=mem_file)

    mem.remember("key1", "val1")
    mem.log_event("custom_event", detail="test")
    assert len(mem.history()) >= 2

    mem.clear()
    assert mem.list_facts() == {}
    assert mem.history() == []


def test_memory_export_import(tmp_path):
    mem_file1 = os.path.join(tmp_path, "mem1.json")
    mem_file2 = os.path.join(tmp_path, "mem2.json")
    export_file = os.path.join(tmp_path, "export.json")

    mem1 = MemoryAI(path=mem_file1)
    mem1.remember("db", "postgresql", tags=["database"], category="infra")
    mem1.add_node("n1", "service", "API")
    mem1.link("n1", "n2", "calls")
    mem1.export_memory(export_file)

    assert os.path.exists(export_file)

    mem2 = MemoryAI(path=mem_file2)
    mem2.remember("cache", "redis")
    mem2.import_memory(export_file, merge=True)

    assert mem2.recall("db") == "postgresql"
    assert mem2.recall("cache") == "redis"
    assert mem2.get_fact_meta("db") == {"tags": ["database"], "category": "infra"}
    assert len(mem2.graph()["nodes"]) == 1


def test_memory_cli_commands(tmp_path, capsys):
    mem_file = os.path.join(tmp_path, "memory.json")

    # We monkeypatch MemoryAI default path or use CLI flags if available.
    # Since MemoryAI() uses default path, let's point default or test via MemoryAI directly.
    import chief_ai.cli as cli_module

    original_memory_ai = cli_module.MemoryAI
    try:
        cli_module.MemoryAI = lambda path=mem_file: original_memory_ai(path=mem_file)

        # chief memory add
        rc = main(["memory", "add", "os", "linux", "--tag", "sys,admin", "--category", "ops"])
        assert rc == 0

        # chief memory list
        rc = main(["memory", "list"])
        assert rc == 0
        captured = capsys.readouterr().out
        assert "os: linux" in captured

        # chief memory query
        rc = main(["memory", "query", "linux"])
        assert rc == 0
        captured = capsys.readouterr().out
        assert "os: linux" in captured

        # chief memory export
        exp_path = os.path.join(tmp_path, "cli_exp.json")
        rc = main(["memory", "export", exp_path])
        assert rc == 0
        assert os.path.exists(exp_path)

        # chief memory remove
        rc = main(["memory", "remove", "os"])
        assert rc == 0

        # chief memory list (empty)
        rc = main(["memory", "list"])
        assert rc == 0
        captured = capsys.readouterr().out
        assert "No memory facts found." in captured

        # chief memory import
        rc = main(["memory", "import", exp_path])
        assert rc == 0

        # chief memory list (restored)
        rc = main(["memory", "list"])
        assert rc == 0
        captured = capsys.readouterr().out
        assert "os: linux" in captured

        # chief memory clear
        rc = main(["memory", "clear"])
        assert rc == 0

    finally:
        cli_module.MemoryAI = original_memory_ai
