"""Tests for MemoryAI storage, persistence, categories, deletion, and graph capabilities."""

from __future__ import annotations

from chief_ai.core.memory import MemoryAI


def test_memory_json_backend(tmp_path) -> None:
    path = str(tmp_path / "memory.json")
    mem1 = MemoryAI(path=path)
    mem1.remember("project_name", "Chief-AI", category="meta")
    mem1.log_event("init", "created project")
    mem1.add_node("n1", "system", "Chief AI")
    mem1.link("n1", "n2", "depends_on")

    # Reload from same file
    mem2 = MemoryAI(path=path)
    assert mem2.recall("project_name") == "Chief-AI"
    assert mem2.recall_by_category("meta") == {"project_name": "Chief-AI"}
    assert len(mem2.history()) == 2  # fact + init event
    g = mem2.graph()
    assert len(g["nodes"]) == 1
    assert len(g["edges"]) == 1


def test_memory_sqlite_backend(tmp_path) -> None:
    path = str(tmp_path / "memory.sqlite")
    mem1 = MemoryAI(path=path)
    assert mem1.backend == "sqlite"

    mem1.remember("backend", "fastapi", category="architecture")
    mem1.remember("database", "sqlite", category="architecture")
    mem1.log_event("setup", "database initialized")
    mem1.add_node("db1", "database", "SQLite")

    # Reload from same SQLite file
    mem2 = MemoryAI(path=path)
    assert mem2.recall("backend") == "fastapi"
    assert mem2.recall("database") == "sqlite"
    assert mem2.recall_by_category("architecture") == {
        "backend": "fastapi",
        "database": "sqlite",
    }
    assert len(mem2.history()) == 3  # 2 facts + setup event
    g = mem2.graph()
    assert len(g["nodes"]) == 1
    assert g["nodes"][0]["id"] == "db1"


def test_memory_remember_recall_and_categories(tmp_path) -> None:
    path = str(tmp_path / "mem.json")
    mem = MemoryAI(path=path)

    mem.remember("k1", "v1", category="catA")
    mem.remember("k2", "v2", category="catB")
    mem.remember("k3", "v3", category="catA")

    assert mem.recall("k1") == "v1"
    assert mem.recall("non_existent") is None

    cat_a = mem.recall_by_category("catA")
    assert cat_a == {"k1": "v1", "k3": "v3"}

    # Update category
    mem.remember("k1", "v1_updated", category="catB")
    assert mem.recall("k1") == "v1_updated"
    assert mem.recall_by_category("catA") == {"k3": "v3"}
    assert "k1" in mem.recall_by_category("catB")


def test_memory_forget_and_clear(tmp_path) -> None:
    path = str(tmp_path / "mem.json")
    mem = MemoryAI(path=path)

    mem.remember("k1", "v1", category="temp")
    mem.remember("k2", "v2", category="temp")
    assert mem.recall("k1") == "v1"

    # Forget existing key
    assert mem.forget("k1") is True
    assert mem.recall("k1") is None
    assert "k1" not in mem.recall_by_category("temp")

    # Forget non-existent key returns False
    assert mem.forget("k1") is False

    # Clear memory state
    mem.add_node("n1", "kind1", "label1")
    mem.clear()
    assert mem.recall("k2") is None
    assert mem.history() == []
    assert mem.graph()["nodes"] == []


def test_memory_graph_and_history(tmp_path) -> None:
    path = str(tmp_path / "graph.json")
    mem = MemoryAI(path=path)

    mem.add_node("n1", "user", "Alice")
    mem.add_node("n2", "agent", "Chief")
    mem.link("n1", "n2", "talks_to")

    g = mem.graph()
    assert len(g["nodes"]) == 2
    assert len(g["edges"]) == 1
    assert g["edges"][0] == {"src": "n1", "dst": "n2", "relation": "talks_to"}

    hits = mem.retrieve("Chief")
    assert len(hits) == 0  # retrieve operates on facts

    mem.remember("agent_role", "Chief AI assistant")
    hits = mem.retrieve("Chief")
    assert len(hits) == 1
    assert "agent_role: Chief AI assistant" in hits[0]


def test_memory_retrieve_relevance_scoring(tmp_path) -> None:
    path = str(tmp_path / "mem.json")
    mem = MemoryAI(path=path)

    mem.remember("fact1", "python language programming")
    mem.remember("fact2", "python web framework fastapi python web")
    mem.remember("fact3", "unrelated entry")

    hits = mem.retrieve("python web framework")
    assert len(hits) == 2
    # fact2 matches all 3 tokens with high frequency, so it ranks first
    assert hits[0].startswith("fact2:")
    assert hits[1].startswith("fact1:")
