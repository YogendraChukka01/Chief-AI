"""Web search tool using Tavily API."""

from typing import Literal

from asyncer import asyncify
from pydantic_ai import RunContext

from libagentic.models import TavilyDeps


async def web_search(
    ctx: RunContext[TavilyDeps],
    query: str,
    search_depth: Literal["basic", "advanced"] | None = None,
    topic: Literal["general", "news", "finance"] | None = None,
    time_range: Literal["day", "week", "month", "year"] | None = None,
    max_results: int | None = None,
    timeout: int = 60,
) -> dict:
    """Perform a web search using the Tavily client.

    Args:
        ctx: The run context containing TavilyDeps
        query: The search query
        search_depth: The depth of the search (basic or advanced)
        topic: The topic category (general, news, finance)
        time_range: The time range for results
        max_results: Maximum number of results to return
        timeout: Request timeout in seconds

    Returns:
        Dictionary containing search results
    """
    return await asyncify(ctx.deps.tavily_client.search)(
        query=query,
        search_depth=search_depth,
        topic=topic,
        time_range=time_range,
        max_results=max_results,
        timeout=timeout,
    )
