"""Memory AI — long-term store, knowledge graph, history, and retrieval.

A small JSON-backed store. In a production system this would sit behind a
vector database; here it is a self-contained, dependency-free implementation
so the orchestrator has persistent context without external services.
"""

from __future__ import annotations

import json
import os
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
    fact_meta: dict[str, dict] = field(default_factory=dict)
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
        try:
            with open(self.path, encoding="utf-8") as fh:
                raw = json.load(fh)
        except (json.JSONDecodeError, OSError):
            return

        raw_facts = raw.get("facts", {})
        facts: dict[str, str] = {}
        fact_meta: dict[str, dict] = raw.get("fact_meta", {})

        for k, v in raw_facts.items():
            if isinstance(v, dict):
                facts[k] = str(v.get("value", ""))
                fact_meta[k] = {
                    "tags": list(v.get("tags", [])),
                    "category": v.get("category"),
                }
            else:
                facts[k] = str(v)

        self._state.facts = facts
        self._state.fact_meta = fact_meta
        self._state.history = raw.get("history", [])
        self._state.nodes = {
            k: _GraphNode(**v) for k, v in raw.get("nodes", {}).items()
        }
        self._state.edges = [_GraphEdge(**e) for e in raw.get("edges", [])]

    def save(self) -> None:
        os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
        raw = {
            "facts": self._state.facts,
            "fact_meta": self._state.fact_meta,
            "history": self._state.history,
            "nodes": {k: vars(v) for k, v in self._state.nodes.items()},
            "edges": [vars(e) for e in self._state.edges],
        }
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(raw, fh, indent=2)

    # -- long-term memory --------------------------------------------------
    def remember(
        self,
        key: str,
        value: str,
        tags: list[str] | None = None,
        category: str | None = None,
    ) -> None:
        self._state.facts[key] = value
        meta: dict = {}
        if tags is not None:
            meta["tags"] = [t.strip().lower() for t in tags if t.strip()]
        if category is not None:
            meta["category"] = category.strip().lower()

        if meta:
            self._state.fact_meta[key] = meta
        elif key in self._state.fact_meta:
            del self._state.fact_meta[key]

        self._state.history.append({"type": "fact", "key": key, "action": "remember"})
        self.save()

    def recall(self, key: str) -> str | None:
        return self._state.facts.get(key)

    def forget(self, key: str) -> bool:
        """Remove a fact and its metadata from memory."""
        existed = key in self._state.facts
        if existed:
            del self._state.facts[key]
            self._state.fact_meta.pop(key, None)
            self._state.history.append({"type": "fact", "key": key, "action": "forget"})
            self.save()
        return existed

    def clear(self) -> None:
        """Clear all stored facts, metadata, history, nodes, and edges."""
        self._state.facts.clear()
        self._state.fact_meta.clear()
        self._state.history.clear()
        self._state.nodes.clear()
        self._state.edges.clear()
        self.save()

    def get_fact_meta(self, key: str) -> dict | None:
        """Return fact metadata (tags and category) if present."""
        return self._state.fact_meta.get(key)

    def list_facts(
        self,
        tag: str | None = None,
        category: str | None = None,
    ) -> dict[str, str]:
        """Return stored facts matching optional tag and category filters."""
        result = {}
        tag_lower = tag.strip().lower() if tag else None
        cat_lower = category.strip().lower() if category else None

        for k, v in self._state.facts.items():
            meta = self._state.fact_meta.get(k, {})
            if tag_lower and tag_lower not in meta.get("tags", []):
                continue
            if cat_lower and cat_lower != meta.get("category"):
                continue
            result[k] = v

        return result

    # -- export & import ---------------------------------------------------
    def export_memory(self, filepath: str) -> None:
        """Export current memory snapshot to a JSON file."""
        os.makedirs(os.path.dirname(filepath) or ".", exist_ok=True)
        raw = {
            "facts": self._state.facts,
            "fact_meta": self._state.fact_meta,
            "history": self._state.history,
            "nodes": {k: vars(v) for k, v in self._state.nodes.items()},
            "edges": [vars(e) for e in self._state.edges],
        }
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(raw, fh, indent=2)

    def import_memory(self, filepath: str, merge: bool = True) -> None:
        """Import memory snapshot from a JSON file."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"Memory export file not found: {filepath}")

        with open(filepath, encoding="utf-8") as fh:
            raw = json.load(fh)

        if not merge:
            self.clear()

        imported_facts = raw.get("facts", {})
        imported_meta = raw.get("fact_meta", {})
        for k, v in imported_facts.items():
            if isinstance(v, dict):
                val = str(v.get("value", ""))
                meta = {
                    "tags": list(v.get("tags", [])),
                    "category": v.get("category"),
                }
            else:
                val = str(v)
                meta = imported_meta.get(k, {})

            self._state.facts[k] = val
            if meta:
                self._state.fact_meta[k] = meta

        self._state.history.extend(raw.get("history", []))
        for k, v in raw.get("nodes", {}).items():
            self._state.nodes[k] = _GraphNode(**v)
        for e in raw.get("edges", []):
            self._state.edges.append(_GraphEdge(**e))

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
        tag: str | None = None,
        category: str | None = None,
    ) -> list[str]:
        """Return facts whose key, value, tags, or category shares terms with ``query``.

        Keys starting with any ``exclude`` prefix are skipped (e.g. per-task
        ``result:`` entries, which should not resurface as prior context).
        """
        import re

        tokens = {t for t in re.findall(r"[a-z0-9]{3,}", query.lower())}
        tag_lower = tag.strip().lower() if tag else None
        cat_lower = category.strip().lower() if category else None

        hits = []
        for k, v in self._state.facts.items():
            if any(k.startswith(p) for p in exclude):
                continue

            meta = self._state.fact_meta.get(k, {})
            if tag_lower and tag_lower not in meta.get("tags", []):
                continue
            if cat_lower and cat_lower != meta.get("category"):
                continue

            tags_str = " ".join(meta.get("tags", []))
            cat_str = meta.get("category") or ""
            hay = f"{k} {v} {tags_str} {cat_str}".lower()

            if not tokens or any(tok in hay for tok in tokens):
                hits.append(f"{k}: {v}")

        return hits[:limit]
