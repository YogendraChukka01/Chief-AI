"""Chen AI psychologist CLI application."""

import asyncio
import os
from os import environ

import typer
from dotenv import load_dotenv
from rich.console import Console
from tavily import TavilyClient

from appclis.settings.settings_manager import SettingsManager
from libagentic.agents import get_chen_agent
from libagentic.logging import get_logger, setup_logger
from libagentic.models import TavilyDeps
from libchatinterface import ChatInterface

logger = get_logger("chen")

load_dotenv()
app = typer.Typer(pretty_exceptions_enable=False)
console = Console()

settings_manager = SettingsManager()


def _set_env_from_settings(settings: object) -> None:
    """Set environment variables from settings for model providers.

    Args:
        settings: Settings object containing API keys
    """
    env_mapping = {
        "anthropic_api_key": "ANTHROPIC_API_KEY",
        "openai_api_key": "OPENAI_API_KEY",
        "openrouter_api_key": "OPENROUTER_API_KEY",
        "tavily_api_key": "TAVILY_API_KEY",
    }

    for attr, env_var in env_mapping.items():
        value = getattr(settings, attr, None)
        if value:
            os.environ[env_var] = value
            logger.debug("Set %s from settings", env_var)


async def run() -> None:
    """Initialize and run the Chen chat interface."""
    try:
        settings = settings_manager.load_settings()
        _set_env_from_settings(settings)

        tavily_api_key = environ.get("TAVILY_API_KEY")
        if not tavily_api_key:
            logger.warning("TAVILY_API_KEY not set, web search disabled")
            console.print("[yellow]Warning: TAVILY_API_KEY not found.[/yellow]")
            console.print("[yellow]Web search functionality will be disabled.[/yellow]")
            deps = None
        else:
            tavily_client = TavilyClient(api_key=tavily_api_key)
            deps = TavilyDeps(tavily_client=tavily_client)

        agent = get_chen_agent(language=settings.language or "English")
        chat_interface = ChatInterface(
            agent=agent,
            deps=deps,
            app_name="chen",
            assistant_name="Chen",
            context_window=settings.context_window or 200000,
        )
        await chat_interface.run_chat()

    except KeyboardInterrupt:
        raise

    except Exception as e:
        logger.exception("Error starting Chen")
        console.print(f"[red]Error starting Chen: {e}[/red]")
        raise


@app.callback(invoke_without_command=True)
def main(ctx: typer.Context) -> None:
    """Start Chen chat interface."""
    if ctx.invoked_subcommand is None:
        try:
            asyncio.run(run())
        except KeyboardInterrupt:
            console.print("\n\n[yellow]Goodbye![/yellow]")


config_app = typer.Typer()
app.add_typer(config_app, name="config")


@config_app.callback(invoke_without_command=True)
def config(ctx: typer.Context) -> None:
    """Show current configuration settings."""
    if ctx.invoked_subcommand is None:
        settings_manager.show_current_settings()


@config_app.command()
def get(key: str) -> None:
    """Get a specific configuration setting value."""
    try:
        value = settings_manager.get_setting(key)
        if value is None:
            console.print(f"[dim]{key}: Not set[/dim]")
        else:
            display_value = f"{str(value)[:8]}..." if key.endswith("_api_key") and len(str(value)) > 8 else str(value)
            console.print(f"[cyan]{key}[/cyan]: [green]{display_value}[/green]")
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


@config_app.command()
def set(key: str, value: str) -> None:
    """Set a specific configuration setting value."""
    try:
        settings_manager.set_setting(key, value)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")


@config_app.command("list")
def list_settings() -> None:
    """List all configuration settings."""
    settings_manager.show_current_settings()


@app.command()
def reset() -> None:
    """Reset all configuration settings."""
    settings_manager.reset_settings()


@app.command()
def onboard() -> None:
    """Run the onboarding process to configure settings."""
    try:
        settings_manager._run_onboarding()
    except KeyboardInterrupt:
        console.print("\n[yellow]Onboarding cancelled.[/yellow]")
    except Exception as e:
        logger.exception("Onboarding failed")
        console.print(f"[red]Onboarding failed: {e}[/red]")


if __name__ == "__main__":
    setup_logger(level="INFO")
    app()
