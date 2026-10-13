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


def test_cli_memory_export_and_import(tmp_path, capsys) -> None:
    mem_path1 = str(tmp_path / "memory1.json")
    export_path = str(tmp_path / "export.json")
    mem_path2 = str(tmp_path / "memory2.json")

    mem1 = MemoryAI(path=mem_path1)
    mem1.remember("key1", "val1", category="test")

    # Export CLI command
    ret = main(["memory", "--path", mem_path1, "export", export_path])
    assert ret == 0
    assert "Exported memory" in capsys.readouterr().out

    # Import CLI command (merge)
    mem2 = MemoryAI(path=mem_path2)
    mem2.remember("key2", "val2")
    ret = main(["memory", "--path", mem_path2, "import", export_path])
    assert ret == 0
    assert "Merged memory store" in capsys.readouterr().out

    mem2_check = MemoryAI(path=mem_path2)
    assert mem2_check.recall("key1") == "val1"
    assert mem2_check.recall("key2") == "val2"

    # Import CLI command (overwrite)
    ret = main(["memory", "--path", mem_path2, "import", export_path, "--overwrite"])
    assert ret == 0
    assert "Overwrote memory store" in capsys.readouterr().out

    mem2_check_overwrite = MemoryAI(path=mem_path2)
    assert mem2_check_overwrite.recall("key1") == "val1"
    assert mem2_check_overwrite.recall("key2") is None
