"""Memory AI — long-term store, knowledge graph, history, and retrieval.

A small JSON-backed store. In a production system this would sit behind a
vector database; here it is a self-contained, dependency-free implementation
so the orchestrator has persistent context without external services.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional


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
    history: list[dict] = field(default_factory=list)
    nodes: dict[str, _GraphNode] = field(default_factory=dict)
    edges: list[_GraphEdge] = field(default_factory=list)


class MemoryAI:
    def __init__(self, path: str = ".chief_memory/memory.json") -> None:
        self.path = path
        self._state = _MemoryState()
        self.load()

    # -- persistence -------------------------------------------------------
    def load(self) -> None:
        if not os.path.exists(self.path):
            return
        with open(self.path, "r", encoding="utf-8") as fh:
            raw = json.load(fh)
        self._state.facts = raw.get("facts", {})
        self._state.history = raw.get("history", [])
        self._state.nodes = {
            k: _GraphNode(**v) for k, v in raw.get("nodes", {}).items()
        }
        self._state.edges = [_GraphEdge(**e) for e in raw.get("edges", [])]

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        raw = {
            "facts": self._state.facts,
            "history": self._state.history,
            "nodes": {k: vars(v) for k, v in self._state.nodes.items()},
            "edges": [vars(e) for e in self._state.edges],
        }
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(raw, fh, indent=2)

    # -- long-term memory --------------------------------------------------
    def remember(self, key: str, value: str) -> None:
        self._state.facts[key] = value
        self._state.history.append({"type": "fact", "key": key})
        self.save()

    def recall(self, key: str) -> Optional[str]:
        return self._state.facts.get(key)

    # -- history -----------------------------------------------------------
    def log_event(self, event: str, detail: Optional[str] = None) -> None:
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
    def retrieve(self, query: str, limit: int = 5, exclude: tuple[str, ...] = ()) -> list[str]:
        """Return facts whose key or value shares a meaningful term with ``query``.

        Keys starting with any ``exclude`` prefix are skipped (e.g. per-task
        ``result:`` entries, which should not resurface as prior context).
        """
        import re

        tokens = {t for t in re.findall(r"[a-z0-9]{3,}", query.lower())}
        if not tokens:
            return []
        hits = []
        for k, v in self._state.facts.items():
            if any(k.startswith(p) for p in exclude):
                continue
            hay = f"{k} {v}".lower()
            if any(tok in hay for tok in tokens):
                hits.append(f"{k}: {v}")
        return hits[:limit]
