"""Chief AI agent CLI application."""

import asyncio

import typer
from rich.console import Console

from libagentic.agents import get_chief_agent
from libagentic.logging import get_logger, setup_logger

logger = get_logger("chief")

app = typer.Typer(pretty_exceptions_enable=False)


async def run() -> None:
    """Initialize and run the Chief agent."""
    agent = get_chief_agent()
    await agent.to_cli(prog_name="Chief")


@app.command()
def main() -> None:
    """Start Chief AI agent."""
    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        console = Console()
        console.print("\n\n[yellow]Goodbye![/yellow]")
    except Exception as e:
        logger.exception("Error starting Chief")
        console = Console()
        console.print(f"[red]Error starting Chief: {e}[/red]")
        raise


if __name__ == "__main__":
    setup_logger(level="INFO")
    app()
