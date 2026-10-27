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


def test_cli_run_export_json(tmp_path) -> None:
    export_path = str(tmp_path / "report.json")
    ret = main(["run", "Build a landing page", "--export-json", export_path])
    assert ret == 0

    import json

    with open(export_path, encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["goal"] == "Build a landing page"
    assert "tasks" in data
    assert "results" in data


def test_cli_export_command(tmp_path, capsys) -> None:
    # Test stdout output
    ret = main(["export", "Build a landing page"])
    assert ret == 0
    out = capsys.readouterr().out
    assert "Build a landing page" in out

    # Test file export
    export_path = str(tmp_path / "export_cmd_report.json")
    ret = main(["export", "Build a landing page", "--out", export_path])
    assert ret == 0

    import json

    with open(export_path, encoding="utf-8") as fh:
        data = json.load(fh)
    assert data["goal"] == "Build a landing page"
