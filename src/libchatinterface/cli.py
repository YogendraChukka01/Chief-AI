"""Rich-based chat interface components with history support."""

import asyncio
import contextlib
import json
import os
import re
import sys
from collections.abc import AsyncIterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic_ai.messages import (
    ModelRequest,
    AgentStreamEvent,
    FunctionToolCallEvent,
    FunctionToolResultEvent,
)
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.text import Text

from libchatinterface.costs import format_token_count


class HistoryManager:
    """Manages command history storage using Pydantic ModelRequest format."""

    def __init__(self, app_name: str = "chatinterface"):
        self.history_dir = Path.home() / f".{app_name}"
        self.history_file = self.history_dir / "history.jsonl"
        self.history: list[str] = []
        self._ensure_directory()
        self._load_history()

    def _ensure_directory(self):
        """Create ~/.{app_name} directory if it doesn't exist."""
        self.history_dir.mkdir(exist_ok=True)

    def _load_history(self):
        """Load command history from file."""
        if not self.history_file.exists():
            return

        try:
            with self.history_file.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        data = json.loads(line)
                        if data.get("type") == "user_prompt" and "content" in data:
                            content = data["content"]
                            model_request = data.get("model_request")
                            if isinstance(model_request, dict):
                                self.history.append(content)
                            elif isinstance(model_request, str) and model_request.startswith("ModelRequest("):
                                self.history.append(content)
                            else:
                                self.history.append(content)
        except Exception:
            self.history = []

    def add_message(self, message: str):
        """Add a user message to history."""
        if message.strip() and message not in ["/quit", "/exit", "/help", "quit", "exit", "help"]:
            model_request = ModelRequest.user_text_prompt(message)

            try:
                model_request_data = {"kind": getattr(model_request, "kind", "user"), "parts": []}
                for part in model_request.parts:
                    part_data = {
                        "part_kind": getattr(part, "part_kind", "user_prompt"),
                        "content": part.content,
                        "timestamp": part.timestamp.isoformat() if part.timestamp else None,
                    }
                    model_request_data["parts"].append(part_data)
            except Exception:
                model_request_data = {
                    "kind": "user",
                    "parts": [
                        {
                            "part_kind": "user_prompt",
                            "content": message,
                            "timestamp": datetime.now(UTC).isoformat(),
                        }
                    ],
                    "serialization_fallback": True,
                }

            history_entry = {
                "timestamp": datetime.now(UTC).isoformat(),
                "type": "user_prompt",
                "content": message,
                "model_request": model_request_data,
            }

            self.history.append(message)

            try:
                with self.history_file.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(history_entry, ensure_ascii=False) + "\n")
            except Exception:
                pass

    def get_history(self) -> list[str]:
        """Get the command history list."""
        return self.history.copy()


class RichHistoryPrompt:
    """Rich-native prompt with command history navigation."""

    def __init__(self, console: Console, history_manager: HistoryManager):
        self.console = console
        self.history_manager = history_manager
        self.history_index = -1
        self.current_input = ""
        self.original_input = ""

    def _get_char(self) -> str:
        """Get a single character from stdin."""
        if os.name == "nt":
            import msvcrt
            return msvcrt.getch().decode("utf-8", errors="ignore")
        else:
            import termios
            import tty
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.cbreak(fd)
                ch = sys.stdin.read(1)
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

    def _handle_arrow_keys(self, char: str) -> str | None:
        """Handle arrow key sequences."""
        if char == "\x1b":
            try:
                next_chars = sys.stdin.read(2)
                if next_chars == "[A":
                    return self._navigate_history(-1)
                elif next_chars == "[B":
                    return self._navigate_history(1)
            except Exception:
                pass
        return None

    def _navigate_history(self, direction: int) -> str:
        """Navigate through command history."""
        history = self.history_manager.get_history()
        if not history:
            return self.current_input

        if self.history_index == -1:
            self.original_input = self.current_input

        new_index = self.history_index + direction

        if direction == 1 and new_index >= 0:
            self.history_index = -1
            return self.original_input
        elif direction == -1 and abs(new_index) <= len(history):
            self.history_index = new_index
            return history[new_index]

        return self.current_input

    def ask(self, prompt: str) -> str:
        """Rich-styled prompt with history navigation."""
        self.history_index = -1
        self.current_input = ""
        self.original_input = ""

        self.console.print(f"{prompt} [dim](up/down for history)[/dim]")

        try:
            import readline
            readline.clear_history()
            for item in self.history_manager.get_history():
                readline.add_history(item)
            result = input().strip()
        except ImportError:
            result = Prompt.ask("", console=self.console).strip()

        return result


class MarkdownRenderer:
    """Handles markdown rendering with support for nested markdown code blocks."""

    def __init__(self, console: Console):
        self.console = console

    def render(self, content: str) -> None:
        """Render markdown content."""
        nested_pattern = r"```markdown\s*\n(.*?)```"
        matches = list(re.finditer(nested_pattern, content, re.DOTALL))

        if not matches:
            md = Markdown(content)
            self.console.print(md)
            return

        current_pos = 0
        for match in matches:
            if current_pos < match.start():
                pre_content = content[current_pos : match.start()]
                if pre_content.strip():
                    md = Markdown(pre_content)
                    self.console.print(md)

            nested_content = match.group(1)
            if nested_content.strip():
                nested_md = Markdown(nested_content)
                panel = Panel(nested_md, title="Markdown Content", border_style="blue")
                self.console.print(panel)

            current_pos = match.end()

        if current_pos < len(content):
            remaining_content = content[current_pos:]
            if remaining_content.strip():
                md = Markdown(remaining_content)
                self.console.print(md)


class ChatInterface:
    """Generic chat interface using Rich for rendering with history support."""

    def __init__(
        self,
        agent: Any,
        deps: Any = None,
        app_name: str = "chatinterface",
        assistant_name: str = "Assistant",
        context_window: int = 200_000,
    ):
        self.agent = agent
        self.deps = deps
        self.app_name = app_name
        self.assistant_name = assistant_name
        self.console = Console()
        self.renderer = MarkdownRenderer(self.console)
        self.history_manager = HistoryManager(app_name)
        self.history_prompt = RichHistoryPrompt(self.console, self.history_manager)
        self.running = True

        from libchatinterface.session import SessionManager
        self.session_manager = SessionManager(app_name, context_window=context_window)

        system_prompt = getattr(agent, "system_prompt", None)
        if system_prompt:
            self.session_manager.log_system_prompt(system_prompt)

    async def _tool_event_handler(self, ctx, event_stream: AsyncIterable[AgentStreamEvent]):
        """Handle tool events and display them to user in real-time."""
        async for event in event_stream:
            if isinstance(event, FunctionToolCallEvent):
                tool_name = event.part.tool_name
                if tool_name == "web_search":
                    if isinstance(event.part.args, dict):
                        query = event.part.args.get("query", "unknown query")
                    elif isinstance(event.part.args, str):
                        query = event.part.args
                    else:
                        query = "unknown query"
                    self.console.print(f"[dim cyan]Searching the web for: {query}[/dim cyan]")
                else:
                    self.console.print(f"[dim cyan]Using tool: {tool_name}[/dim cyan]")
            elif isinstance(event, FunctionToolResultEvent):
                self.console.print(f"[dim green]Tool completed successfully[/dim green]")

    def show_welcome(self):
        """Display welcome message."""
        welcome_text = Text(f"{self.assistant_name} AI Assistant", style="bold blue")
        welcome_panel = Panel(
            welcome_text,
            subtitle="Type your message, '/quit' to exit, or use up/down arrows for history",
            border_style="blue",
        )
        self.console.print(welcome_panel)
        self.console.print()

    def get_user_input(self) -> str:
        """Get input from user with rich prompt and history navigation."""
        try:
            user_input = self.history_prompt.ask("[bold green]You[/bold green]")
            return user_input.strip()
        except EOFError:
            return "/quit"
        except KeyboardInterrupt:
            raise

    async def _background_title_generation(self) -> None:
        """Generate AI title in background."""
        with contextlib.suppress(Exception):
            await self.session_manager.update_title_with_ai()

    def _prepare_agent_with_context(self) -> Any:
        """Prepare agent with compressed context if available."""
        if not self.session_manager.compressed_context:
            return self.agent

        from pydantic_ai import Agent
        original_prompt = getattr(self.agent, "system_prompt", "")
        extended_prompt = f"{original_prompt}\n\nPrevious Session Context: {self.session_manager.compressed_context}"

        return Agent(
            model=self.agent.model,
            name=self.agent.name,
            system_prompt=extended_prompt,
            deps_type=getattr(self.agent, "deps_type", None),
            toolsets=getattr(self.agent, "toolsets", []),
            model_settings=getattr(self.agent, "model_settings", None),
            mcp_servers=getattr(self.agent, "mcp_servers", None),
        )

    def show_usage_metadata(self) -> None:
        """Display session usage metadata."""
        if self.session_manager.message_count == 0:
            return

        session_costs = self.session_manager.session_costs
        total = session_costs.total_usage

        if total.total_tokens == 0:
            return

        self.console.rule(style="dim")
        usage_parts = []

        if total.input_tokens > 0 or total.output_tokens > 0:
            tokens_text = (
                f"Tokens: {format_token_count(total.input_tokens)} in, {format_token_count(total.output_tokens)} out"
            )
            if total.cached_tokens > 0:
                tokens_text += f", {format_token_count(total.cached_tokens)} cached"
            tokens_text += f" ({format_token_count(total.total_tokens)} total)"
            usage_parts.append(tokens_text)

        if total.requests > 0:
            usage_parts.append(f"Requests: {total.requests}")

        if total.cost_usd is not None and total.cost_usd > 0:
            cost_text = "Cost: <$0.01" if total.cost_usd < 0.01 else f"Cost: ${total.cost_usd:.4f}"
            usage_parts.append(cost_text)

        if usage_parts:
            usage_text = " * ".join(usage_parts)
            self.console.print(f"[dim]{usage_text}[/dim]")

    def handle_command(self, user_input: str) -> bool:
        """Handle special commands. Returns False if should exit."""
        if user_input.lower() in ["/quit", "/exit", "quit", "exit"]:
            self.console.print("[yellow]Goodbye![/yellow]")
            return False
        elif user_input.lower() in ["/help", "help"]:
            help_text = f"""
Available commands:
- /quit, /exit: Exit the chat
- /resume: Resume a previous chat session
- /help: Show this help message
- Any other text: Send message to {self.assistant_name} AI
"""
            self.console.print(Panel(help_text.strip(), title="Help", border_style="yellow"))
            return True
        elif user_input.lower() == "/resume":
            return self._handle_resume_command()
        return True

    def _handle_resume_command(self) -> bool:
        """Handle the /resume command."""
        from libchatinterface.session import ResumableSessionManager, SessionLister

        try:
            lister = SessionLister(self.app_name)
            selected_session_dir = lister.show_session_selection(self.console)

            if selected_session_dir is None:
                self.console.print("[yellow]Resume cancelled.[/yellow]")
                return True

            resumed_manager = ResumableSessionManager.from_existing_session(
                selected_session_dir, self.app_name, context_window=self.session_manager.context_window
            )

            session_info = resumed_manager.get_session_info()
            self.console.print(f"[green]Resumed session: {session_info['title']}[/green]")
            self.console.print(
                f"[dim]Messages: {session_info['message_count']}, Last activity: {session_info['last_message_timestamp'] or 'Unknown'}[/dim]"
            )

            self.session_manager = resumed_manager
            self._display_conversation_history()
            return True

        except Exception as e:
            self.console.print(f"[red]Error resuming session: {str(e)}[/red]")
            return True

    def _display_conversation_history(self) -> None:
        """Display conversation history from resumed session."""
        messages = self.session_manager.get_conversation_context()

        if not messages:
            self.console.print("[dim]No previous messages to display.[/dim]")
            return

        self.console.print()
        self.console.print("[bold blue]Conversation History:[/bold blue]")
        self.console.print()

        for message in messages:
            msg_type = message.get("type", "unknown")
            content = message.get("content", "")

            if msg_type == "system_prompt":
                continue

            if msg_type == "user_message":
                self.console.print(f"[bold green]You:[/bold green] {content}")
                self.console.print()
            elif msg_type == "assistant_response":
                self.console.print(f"[bold blue]{self.assistant_name}:[/bold blue] {content}")
                self.console.print()
            elif msg_type == "context_compression":
                self.console.print(f"[yellow]{content}[/yellow]")
                self.console.print()

        self.console.print("[dim]--- End of history ---[/dim]")
        self.console.print()

    async def send_message(self, message: str) -> str:
        """Send message to agent and get response using streaming."""
        try:
            self.console.print("\n")

            with self.console.status("[bold blue]Processing message...") as status:
                self.session_manager.log_user_message(message)
                await self.session_manager.compress_context_if_needed()

                if not hasattr(self, "_title_generated"):
                    self._title_generated = True
                    asyncio.create_task(self._background_title_generation())

                status.update("[bold blue]Initializing agent...")
                current_agent = self._prepare_agent_with_context()
                status.update("[bold blue]Awaiting response...")

                message_history = []
                if hasattr(self.session_manager, "get_pydantic_message_history"):
                    all_history = self.session_manager.get_pydantic_message_history()
                    if all_history and len(all_history) > 0:
                        last_msg = all_history[-1]
                        if (hasattr(last_msg, 'parts') and len(last_msg.parts) > 0 and
                            hasattr(last_msg.parts[0], 'content') and
                            last_msg.parts[0].content == message):
                            message_history = all_history[:-1]
                        else:
                            message_history = all_history
                    else:
                        message_history = all_history

                might_use_tools = any(keyword in message.lower() for keyword in [
                    'search', 'web', 'internet', 'find', 'look up', 'latest', 'current',
                    'price', 'weather', 'news', 'time', 'date'
                ])

                if might_use_tools:
                    status.update("[bold blue]Processing request...")
                    result = await current_agent.run(
                        message,
                        deps=self.deps,
                        message_history=message_history
                    )
                    class DummyStreamContext:
                        def __init__(self, run_result):
                            self.result = run_result
                        async def __aenter__(self):
                            return self
                        async def __aexit__(self, *args):
                            pass
                        async def stream_text(self, delta=False, debounce_by=0):
                            yield self.result.output
                        def all_messages(self):
                            return self.result.all_messages()
                        def usage(self):
                            return self.result.usage()

                    stream_context = DummyStreamContext(result)
                    result = stream_context
                else:
                    stream_context = current_agent.run_stream(
                        message,
                        deps=self.deps,
                        message_history=message_history,
                        event_stream_handler=self._tool_event_handler
                    )
                    result = await stream_context.__aenter__()

            try:
                self.console.print()
                self.console.print(f"[bold blue]{self.assistant_name}:[/bold blue]")

                full_response = ""
                try:
                    async for text_delta in result.stream_text(delta=True, debounce_by=0.01):
                        self.console.print(text_delta, end="", markup=True, highlight=False)
                        full_response += text_delta
                except GeneratorExit:
                    pass
                except Exception as stream_error:
                    self.console.print(f"\n[red]Streaming error: {str(stream_error)}[/red]")

                self.console.print()

                try:
                    run_usage = result.usage()
                    model_name = getattr(result, "model_name", None)
                    if run_usage:
                        self.session_manager.log_run_usage(run_usage, model_name)
                except Exception:
                    pass

                try:
                    all_messages = result.all_messages()
                    if message_history and len(message_history) > 0:
                        new_messages = all_messages[len(message_history):]
                    else:
                        new_messages = [
                            msg
                            for msg in all_messages
                            if not hasattr(self, "_last_message_count")
                            or len(all_messages) > getattr(self, "_last_message_count", 0)
                        ]

                    if new_messages:
                        self.session_manager.log_pydantic_messages(new_messages, skip_user_message=message)
                    else:
                        from pydantic_ai.messages import ModelResponse
                        assistant_responses = [msg for msg in all_messages if isinstance(msg, ModelResponse)]
                        if assistant_responses:
                            latest_response = assistant_responses[-1]
                            self.session_manager.log_pydantic_messages([latest_response])

                    await self.session_manager.compress_context_if_needed()
                    self._last_message_count = len(all_messages)
                except Exception:
                    if full_response:
                        self.session_manager.log_assistant_response(full_response)
                        await self.session_manager.compress_context_if_needed()
            finally:
                await stream_context.__aexit__(None, None, None)
                await self.session_manager.compress_context_if_needed()

            return full_response

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Interrupted by user[/yellow]")
            raise
        except Exception as e:
            self.console.print()
            self.console.print(f"[bold blue]{self.assistant_name}:[/bold blue]")
            self.console.print(f"[red]Error: {str(e)}[/red]")

            error_msg = f"Error: {str(e)}"
            self.session_manager.log_assistant_response(error_msg)
            await self.session_manager.compress_context_if_needed()

            return error_msg

    async def run_chat(self):
        """Main chat loop with streaming support."""
        self.show_welcome()

        while self.running:
            user_input = self.get_user_input()

            if not user_input:
                continue

            if user_input.startswith("/") or user_input.lower() in ["quit", "exit", "help"]:
                self.running = self.handle_command(user_input)
                continue

            self.history_manager.add_message(user_input)

            try:
                await self.send_message(user_input)
            except KeyboardInterrupt:
                raise

            self.show_usage_metadata()
            self.console.print()
