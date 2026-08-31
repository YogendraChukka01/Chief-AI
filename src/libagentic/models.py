"""Data models for agent dependencies."""

from dataclasses import dataclass

from tavily import TavilyClient  # type: ignore[import-untyped]


@dataclass
class TavilyDeps:
    """Dependencies for Tavily web search tool."""

    tavily_client: TavilyClient
