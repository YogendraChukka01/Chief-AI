"""Memory AI — long-term store, knowledge graph, history, and retrieval.

A small JSON or SQLite backed store. In a production system this would sit behind a
vector database; here it is a self-contained, dependency-free implementation
so the orchestrator has persistent context without external services.
"""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass, field


@dataclass
class _GraphNode:
    id: str
    kind: str
    label: str


@dataclass
class _GraphEdge:
    src: str
    dst: str
    relation: str


@dataclass
class _MemoryState:
    facts: dict[str, str] = field(default_factory=dict)
    categories: dict[str, str] = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)
    nodes: dict[str, _GraphNode] = field(default_factory=dict)
    edges: list[_GraphEdge] = field(default_factory=list)


class MemoryAI:
    def __init__(
        self,
        path: str = ".chief_memory/memory.json",
        backend: str | None = None,
    ) -> None:
        self.path = path
        if backend is not None:
            self.backend = backend.lower()
        elif self.path.endswith((".db", ".sqlite", ".sqlite3")):
            self.backend = "sqlite"
        else:
            self.backend = "json"

        self._state = _MemoryState()
        self.load()

    # -- persistence -------------------------------------------------------
    def load(self) -> None:
        if self.backend == "sqlite":
            self._load_sqlite()
        else:
            self._load_json()

    def save(self) -> None:
        if self.backend == "sqlite":
            self._save_sqlite()
        else:
            self._save_json()

    def _load_json(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, encoding="utf-8") as fh:
                raw = json.load(fh)
        except (json.JSONDecodeError, OSError):
            return
        self._state.facts = raw.get("facts", {})
        self._state.categories = raw.get("categories", {})
        self._state.history = raw.get("history", [])
        self._state.nodes = {
            k: _GraphNode(**v) for k, v in raw.get("nodes", {}).items()
        }
        self._state.edges = [_GraphEdge(**e) for e in raw.get("edges", [])]

    def _save_json(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        raw = {
            "facts": self._state.facts,
            "categories": self._state.categories,
            "history": self._state.history,
            "nodes": {k: vars(v) for k, v in self._state.nodes.items()},
            "edges": [vars(e) for e in self._state.edges],
        }
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(raw, fh, indent=2)

    def _load_sqlite(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            conn = sqlite3.connect(self.path)
            cur = conn.cursor()

            # Facts table
            cur.execute(
                "CREATE TABLE IF NOT EXISTS facts "
                "(key TEXT PRIMARY KEY, value TEXT, category TEXT)"
            )
            cur.execute("SELECT key, value, category FROM facts")
            for k, v, cat in cur.fetchall():
                self._state.facts[k] = v
                if cat:
                    self._state.categories[k] = cat

            # History table
            cur.execute(
                "CREATE TABLE IF NOT EXISTS history "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT)"
            )
            cur.execute("SELECT payload FROM history ORDER BY id ASC")
            self._state.history = [json.loads(row[0]) for row in cur.fetchall()]

            # Nodes table
            cur.execute(
                "CREATE TABLE IF NOT EXISTS nodes "
                "(id TEXT PRIMARY KEY, kind TEXT, label TEXT)"
            )
            cur.execute("SELECT id, kind, label FROM nodes")
            self._state.nodes = {r[0]: _GraphNode(r[0], r[1], r[2]) for r in cur.fetchall()}

            # Edges table
            cur.execute(
                "CREATE TABLE IF NOT EXISTS edges "
                "(src TEXT, dst TEXT, relation TEXT)"
            )
            cur.execute("SELECT src, dst, relation FROM edges")
            self._state.edges = [_GraphEdge(r[0], r[1], r[2]) for r in cur.fetchall()]

            conn.close()
        except sqlite3.Error:
            return

    def _save_sqlite(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        conn = sqlite3.connect(self.path)
        cur = conn.cursor()

        cur.execute(
            "CREATE TABLE IF NOT EXISTS facts "
            "(key TEXT PRIMARY KEY, value TEXT, category TEXT)"
        )
        cur.execute("DELETE FROM facts")
        for k, v in self._state.facts.items():
            cat = self._state.categories.get(k)
            cur.execute(
                "INSERT INTO facts (key, value, category) VALUES (?, ?, ?)",
                (k, v, cat),
            )

        cur.execute(
            "CREATE TABLE IF NOT EXISTS history "
            "(id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT)"
        )
        cur.execute("DELETE FROM history")
        for h in self._state.history:
            cur.execute("INSERT INTO history (payload) VALUES (?)", (json.dumps(h),))

        cur.execute(
            "CREATE TABLE IF NOT EXISTS nodes "
            "(id TEXT PRIMARY KEY, kind TEXT, label TEXT)"
        )
        cur.execute("DELETE FROM nodes")
        for node in self._state.nodes.values():
            cur.execute(
                "INSERT INTO nodes (id, kind, label) VALUES (?, ?, ?)",
                (node.id, node.kind, node.label),
            )

        cur.execute(
            "CREATE TABLE IF NOT EXISTS edges "
            "(src TEXT, dst TEXT, relation TEXT)"
        )
        cur.execute("DELETE FROM edges")
        for edge in self._state.edges:
            cur.execute(
                "INSERT INTO edges (src, dst, relation) VALUES (?, ?, ?)",
                (edge.src, edge.dst, edge.relation),
            )

        conn.commit()
        conn.close()

    # -- long-term memory --------------------------------------------------
    def remember(self, key: str, value: str, category: str | None = None) -> None:
        self._state.facts[key] = value
        if category:
            self._state.categories[key] = category
        elif key in self._state.categories:
            del self._state.categories[key]
        self._state.history.append({"type": "fact", "key": key, "category": category})
        self.save()

    def recall(self, key: str) -> str | None:
        return self._state.facts.get(key)

    def recall_by_category(self, category: str) -> dict[str, str]:
        return {
            k: v
            for k, v in self._state.facts.items()
            if self._state.categories.get(k) == category
        }

    def forget(self, key: str) -> bool:
        if key not in self._state.facts:
            return False
        del self._state.facts[key]
        self._state.categories.pop(key, None)
        self._state.history.append({"type": "forget", "key": key})
        self.save()
        return True

    def clear(self) -> None:
        self._state = _MemoryState()
        self.save()

    # -- history -----------------------------------------------------------
    def log_event(self, event: str, detail: str | None = None) -> None:
        self._state.history.append({"event": event, "detail": detail})
        self.save()

    def history(self) -> list[dict]:
        return list(self._state.history)

    # -- knowledge graph ---------------------------------------------------
    def add_node(self, node_id: str, kind: str, label: str) -> None:
        self._state.nodes[node_id] = _GraphNode(node_id, kind, label)
        self.save()

    def link(self, src: str, dst: str, relation: str) -> None:
        self._state.edges.append(_GraphEdge(src, dst, relation))
        self.save()

    def graph(self) -> dict:
        return {
            "nodes": [vars(n) for n in self._state.nodes.values()],
            "edges": [vars(e) for e in self._state.edges],
        }

    # -- context retrieval -------------------------------------------------
    def retrieve(
        self,
        query: str,
        limit: int = 5,
        exclude: tuple[str, ...] = (),
        category: str | None = None,
    ) -> list[str]:
        """Return facts matching query terms, sorted by relevance score.

        Keys starting with any ``exclude`` prefix are skipped.
        If ``category`` is specified, only facts in that category are considered.
        """
        import re

        tokens = {t for t in re.findall(r"[a-z0-9]{3,}", query.lower())}
        if not tokens:
            return []

        scored: list[tuple[int, str]] = []
        for k, v in self._state.facts.items():
            if any(k.startswith(p) for p in exclude):
                continue
            if category is not None and self._state.categories.get(k) != category:
                continue

            hay = f"{k} {v}".lower()
            hay_tokens = re.findall(r"[a-z0-9]{3,}", hay)
            score = sum(hay_tokens.count(tok) for tok in tokens)
            if score > 0:
                scored.append((score, f"{k}: {v}"))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [hit for _, hit in scored[:limit]]
