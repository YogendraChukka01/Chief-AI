"""Tests for Chief AI command line interface, including memory subcommands."""

from __future__ import annotations

from chief_ai.cli import main
from chief_ai.core.memory import MemoryAI


def test_cli_memory_list(tmp_path, capsys) -> None:
    mem_path = str(tmp_path / "memory.json")
    mem = MemoryAI(path=mem_path)
    mem.remember("framework", "pydantic-ai", category="core")
    mem.add_node("n1", "system", "Chief AI")

    ret = main(["memory", "--path", mem_path, "list"])
    assert ret == 0

    captured = capsys.readouterr().out
    assert "Memory store" in captured
    assert "framework [core]: pydantic-ai" in captured
    assert "Node n1 (system): Chief AI" in captured


def test_cli_memory_forget(tmp_path, capsys) -> None:
    mem_path = str(tmp_path / "memory.json")
    mem = MemoryAI(path=mem_path)
    mem.remember("k1", "v1")

    # Forget existing key
    ret = main(["memory", "--path", mem_path, "forget", "k1"])
    assert ret == 0
    captured = capsys.readouterr().out
    assert "Forgot fact with key: 'k1'" in captured

    # Forget non-existent key
    ret = main(["memory", "--path", mem_path, "forget", "nonexistent"])
    assert ret == 0
    captured = capsys.readouterr().out
    assert "Key not found in memory: 'nonexistent'" in captured


def test_cli_memory_clear(tmp_path, capsys) -> None:
    mem_path = str(tmp_path / "memory.json")
    mem = MemoryAI(path=mem_path)
    mem.remember("k1", "v1")
    mem.remember("k2", "v2")

    ret = main(["memory", "--path", mem_path, "clear"])
    assert ret == 0
    captured = capsys.readouterr().out
    assert "Cleared all memory" in captured

    # Verify memory is actually cleared
    mem_check = MemoryAI(path=mem_path)
    assert mem_check.recall("k1") is None
    assert mem_check.recall("k2") is None


def test_cli_memory_remember_query_history_export_import(tmp_path, capsys) -> None:
    mem_path = str(tmp_path / "memory.json")
    export_path = str(tmp_path / "export.json")
    import_target_path = str(tmp_path / "imported_memory.json")

    # Remember
    ret = main([
        "memory", "--path", mem_path, "remember", "framework", "pydantic-ai", "--category", "core"
    ])
    assert ret == 0
    captured = capsys.readouterr().out
    assert "Stored fact 'framework' in category 'core' in memory." in captured

    # Query
    ret = main(["memory", "--path", mem_path, "query", "pydantic"])
    assert ret == 0
    captured = capsys.readouterr().out
    assert "Memory query for 'pydantic' returned 1 match(es):" in captured
    assert "framework: pydantic-ai" in captured

    # History
    ret = main(["memory", "--path", mem_path, "history"])
    assert ret == 0
    captured = capsys.readouterr().out
    assert "Memory history" in captured

    # Export
    ret = main(["memory", "--path", mem_path, "export", export_path])
    assert ret == 0
    captured = capsys.readouterr().out
    assert f"Exported memory store data to '{export_path}'." in captured

    # Import into a new store
    ret = main(["memory", "--path", import_target_path, "import", export_path])
    assert ret == 0
    captured = capsys.readouterr().out
    assert f"Merged memory store data from '{export_path}'." in captured

    mem_imported = MemoryAI(path=import_target_path)
    assert mem_imported.recall("framework") == "pydantic-ai"
