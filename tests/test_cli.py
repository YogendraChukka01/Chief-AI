"""Tests for Chief AI command line interface, including memory subcommands."""

from __future__ import annotations

import json

from chief_ai.cli import main
from chief_ai.core.memory import MemoryAI


def test_cli_run_json_output(capsys) -> None:
    ret = main(["run", "Build a landing page", "--json"])
    assert ret == 0
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert data["goal"] == "Build a landing page"
    assert len(data["tasks"]) > 0
    assert len(data["results"]) > 0
    assert "synthesis" in data


def test_cli_run_export_report(tmp_path, capsys) -> None:
    export_path = str(tmp_path / "report.json")
    ret = main(["run", "Build a landing page", "--export", export_path])
    assert ret == 0
    captured = capsys.readouterr().out
    assert f"Execution report saved to {export_path}" in captured

    with open(export_path, encoding="utf-8") as f:
        data = json.load(f)
    assert data["goal"] == "Build a landing page"
    assert len(data["results"]) > 0


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
