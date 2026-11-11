"""Tests for Chief AI command line interface, including memory subcommands."""

from __future__ import annotations

from chief_ai.cli import main
from chief_ai.core.memory import MemoryAI


def test_cli_memory_remember(tmp_path, capsys) -> None:
    mem_path = str(tmp_path / "memory.json")

    # Remember without category
    ret = main(["memory", "--path", mem_path, "remember", "project_name", "Chief-AI"])
    assert ret == 0
    captured = capsys.readouterr().out
    assert "Remembered 'project_name': Chief-AI" in captured

    # Remember with category
    ret = main(
        ["memory", "--path", mem_path, "remember", "backend", "python", "--category", "tech_stack"]
    )
    assert ret == 0
    captured = capsys.readouterr().out
    assert "Remembered 'backend' [tech_stack]: python" in captured

    # Verify directly in store
    mem = MemoryAI(path=mem_path)
    assert mem.recall("project_name") == "Chief-AI"
    assert mem.recall("backend") == "python"
    assert mem.recall_by_category("tech_stack") == {"backend": "python"}


def test_cli_memory_recall(tmp_path, capsys) -> None:
    mem_path = str(tmp_path / "memory.json")
    mem = MemoryAI(path=mem_path)
    mem.remember("k1", "v1", category="test_cat")

    # Recall existing key
    ret = main(["memory", "--path", mem_path, "recall", "k1"])
    assert ret == 0
    captured = capsys.readouterr().out
    assert "k1 [test_cat]: v1" in captured

    # Recall non-existent key
    ret = main(["memory", "--path", mem_path, "recall", "missing_key"])
    assert ret == 0
    captured = capsys.readouterr().out
    assert "Key not found in memory: 'missing_key'" in captured


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
