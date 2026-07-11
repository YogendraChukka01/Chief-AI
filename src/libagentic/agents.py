"""Agent factory functions for creating AI agents."""

from typing import Annotated

from pydantic_ai import Agent, ModelSettings, Tool
from pydantic_ai.mcp import MCPServer
from typing_extensions import Doc

from libagentic.logging import get_logger
from libagentic.prompts import CHEN_SYSTEM_PROMPT, CHIEF_SYSTEM_PROMPT, TITLE_GENERATION_SYSTEM_PROMPT
from libagentic.providers import get_default_model
from libagentic.tools.search import web_search
from libagentic.tools.time import current_datetime

logger = get_logger("agents")


def get_chief_agent(
    mcps: Annotated[list[MCPServer] | None, Doc("List of MCP servers to connect the agent to")] = None,
    temperature: Annotated[float, Doc("Model temperature (lower = less creative)")] = 0.2,
) -> Agent:
    """Create the Chief agent - a barebones agent for custom development.

    Args:
        mcps: List of MCP servers to connect the agent to
        temperature: Model temperature setting

    Returns:
        Configured Chief agent
    """
    settings = ModelSettings(temperature=temperature)
    model = get_default_model()

    logger.info("Creating Chief agent with temperature %.2f", temperature)

    return Agent(
        model,
        name="Chief",
        system_prompt=CHIEF_SYSTEM_PROMPT,
        mcp_servers=mcps,
        model_settings=settings,
    )


def get_chen_agent(
    mcps: Annotated[list[MCPServer] | None, Doc("List of MCP servers to connect the agent to")] = None,
    temperature: Annotated[float, Doc("Model temperature (lower = less creative)")] = 0.2,
    language: Annotated[str, Doc("Language for the AI to use")] = "English",
) -> Agent:
    """Create the Chen agent - an AI psychologist with web search capabilities.

    Args:
        mcps: List of MCP servers to connect the agent to
        temperature: Model temperature setting
        language: Language for the AI to use

    Returns:
        Configured Chen agent
    """
    from libagentic.models import TavilyDeps

    settings = ModelSettings(temperature=temperature)
    model = get_default_model()

    logger.info("Creating Chen agent with language=%s, temperature=%.2f", language, temperature)

    return Agent(
        model,
        name="Chen",
        system_prompt=CHEN_SYSTEM_PROMPT.format(language=language),
        mcp_servers=mcps,
        model_settings=settings,
        deps_type=TavilyDeps,
        tools=[
            Tool(web_search, takes_ctx=True),
            current_datetime,
        ],
    )


def get_title_agent(
    temperature: float = 0.1,
) -> Agent:
    """Create a lightweight agent for generating chat session titles.

    Args:
        temperature: Low temperature for consistent titles

    Returns:
        Configured title generation agent
    """
    settings = ModelSettings(temperature=temperature)
    title_model = get_default_model(
        anthropic_model_name="claude-3-5-haiku-latest",
        openai_model_name="gpt-4o",
        openrouter_model_name="deepseek/deepseek-chat-v3.1:free",
    )

    logger.info("Creating title agent")

    return Agent(
        title_model,
        name="TitleGenerator",
        system_prompt=TITLE_GENERATION_SYSTEM_PROMPT,
        model_settings=settings,
    )


def get_compression_agent() -> Agent:
    """Create a lightweight agent for compressing conversation history.

    Returns:
        Configured context compression agent
    """
    compression_prompt = """You are a context compression specialist. Compress conversation history while:

PRIORITY 1: Preserve meaning over token reduction
PRIORITY 2: Capture nuances and subtleties
PRIORITY 3: Maintain key points and decisions

Output a flowing narrative that preserves:
- Technical decisions and their reasoning
- User preferences and established patterns
- Unresolved issues or pending tasks
- Context needed for future messages"""

    settings = ModelSettings(temperature=0.1)
    model = get_default_model()

    logger.info("Creating compression agent")

    return Agent(
        model,
        name="ContextCompressor",
        system_prompt=compression_prompt,
        model_settings=settings,
    )
