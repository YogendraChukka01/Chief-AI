"""Session management for chat interface with complete message history tracking."""

import contextlib
import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic_ai.messages import ModelMessage, ModelRequest, ModelResponse
from pydantic_ai.usage import RunUsage
from pydantic_core import to_jsonable_python

from rich.console import Console
from uuid_extensions import uuid7str

from libchatinterface.costs import (
    SessionCosts,
    add_usage_to_session,
    calculate_usage_cost,
    format_session_costs_for_metadata,
)


class SessionManager:
    """Manages chat sessions with complete message history and metadata tracking."""

    def __init__(self, app_name: str = "chatinterface", context_window: int | None = None):
        if context_window is None:
            context_window = int(os.getenv("CONTEXT_WINDOW", "200000"))
        self.app_name = app_name
        self.sessions_dir = Path.home() / f".{app_name}" / "sessions"
        self.session_id = uuid7str()
        self.session_timestamp = datetime.now(UTC).isoformat().replace(":", "_")
        self.session_dir = self.sessions_dir / self.session_id
        self.metadata_file = self.session_dir / "metadata.json"
        self.history_file = self.session_dir / "history.jsonl"

        self.first_user_message: str | None = None
        self.message_count = 0
        self.last_message_timestamp: str | None = None
        self.messages: list[dict[str, Any]] = []

        self._session_title: str | None = None
        self._title_generated = False

        self.session_costs = SessionCosts()
        self.context_window = context_window
        self.compressed_context: str | None = None

        # Lazy-load tiktoken to avoid import issues
        self._encoding = None

        self._create_session_directory()

    def _get_encoding(self):
        """Lazy-load tiktoken encoding."""
        if self._encoding is None:
            try:
                import tiktoken
                self._encoding = tiktoken.encoding_for_model("gpt-4")
            except Exception:
                # Fallback: create a simple estimator
                self._encoding = None
        return self._encoding

    def _create_session_directory(self) -> None:
        try:
            self.session_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create session directory: {e}")

    async def _extract_title(self, message: str) -> str:
        try:
            from libagentic.agents import get_title_agent
            title_agent = get_title_agent()
            result = await title_agent.run(f"Generate a title for this message: {message}")
            generated_title = result.output.strip()

            try:
                title_usage = result.usage()
                title_model = getattr(result, "model_name", None)
                if title_usage:
                    self.log_run_usage(title_usage, title_model)
            except Exception:
                pass

            if generated_title.startswith('"') and generated_title.endswith('"'):
                generated_title = generated_title[1:-1].strip()

            if generated_title and len(generated_title.split()) <= 5:
                return generated_title
            else:
                return " ".join(message.split()[:5])

        except Exception as e:
            print(f"AI title generation failed: {e}")
            return self._extract_title_fallback(message)

    def _extract_title_fallback(self, message: str) -> str:
        clean_message = re.sub(r"[^\w\s]", " ", message)
        words = [word for word in clean_message.split() if word.strip()]
        title_words = words[:5]
        if title_words:
            title_words[0] = title_words[0].capitalize()
            return " ".join(title_words)
        return "New Chat"

    def _log_message_to_history(self, message_data: dict[str, Any]) -> None:
        try:
            with self.history_file.open("a", encoding="utf-8") as f:
                json_line = json.dumps(message_data, ensure_ascii=False)
                f.write(json_line + "\n")
        except Exception:
            pass

    def _update_metadata(self, title: str | None = None) -> None:
        with contextlib.suppress(Exception):
            if title and not self._title_generated:
                self._session_title = title
                self._title_generated = True

            current_title = self._session_title or "New Chat"

            metadata = {
                "title": current_title,
                "created_timestamp": self.session_timestamp.replace("_", ":"),
                "message_count": self.message_count,
                "last_message_timestamp": self.last_message_timestamp,
                "usage": format_session_costs_for_metadata(self.session_costs),
            }

            with self.metadata_file.open("w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

    async def update_title_with_ai(self) -> None:
        if not self.first_user_message or self._title_generated:
            return

        try:
            ai_title = await self._extract_title(self.first_user_message)
            self._update_metadata(title=ai_title)
        except Exception:
            fallback_title = self._extract_title_fallback(self.first_user_message)
            self._update_metadata(title=fallback_title)

    def log_run_usage(self, usage: RunUsage, model_name: str | None = None) -> None:
        usage_costs = calculate_usage_cost(usage, model_name)
        add_usage_to_session(self.session_costs, usage_costs)
        self._update_metadata()

    def log_system_prompt(self, system_prompt: str) -> None:
        timestamp = datetime.now(UTC).isoformat()
        message_data = {
            "timestamp": timestamp,
            "type": "system_prompt",
            "content": system_prompt,
            "message_index": self.message_count,
        }
        self.messages.append(message_data)
        self.message_count += 1
        self.last_message_timestamp = timestamp
        self._log_message_to_history(message_data)
        self._update_metadata()

    def log_user_message(self, message: str) -> None:
        timestamp = datetime.now(UTC).isoformat()
        if self.first_user_message is None:
            self.first_user_message = message

        message_data = {
            "timestamp": timestamp,
            "type": "user_message",
            "content": message,
            "message_index": self.message_count,
        }
        self.messages.append(message_data)
        self.message_count += 1
        self.last_message_timestamp = timestamp
        self._log_message_to_history(message_data)
        self._update_metadata()

    def log_assistant_response(self, response: str) -> None:
        timestamp = datetime.now(UTC).isoformat()
        message_data = {
            "timestamp": timestamp,
            "type": "assistant_response",
            "content": response,
            "message_index": self.message_count,
        }
        self.messages.append(message_data)
        self.message_count += 1
        self.last_message_timestamp = timestamp
        self._log_message_to_history(message_data)
        self._update_metadata()

    def log_pydantic_messages(self, pydantic_messages: list[ModelMessage], skip_user_message: str | None = None) -> None:
        for msg in pydantic_messages:
            timestamp = datetime.now(UTC).isoformat()

            if isinstance(msg, ModelRequest):
                for part in msg.parts:
                    if part.__class__.__name__ == "ToolReturnPart":
                        message_data = {
                            "timestamp": timestamp,
                            "type": "tool_return",
                            "content": str(getattr(part, "content", "")),
                            "message_index": self.message_count,
                            "pydantic_type": part.__class__.__name__,
                            "pydantic_data": to_jsonable_python(part),
                        }
                    elif hasattr(part, "content"):
                        if part.__class__.__name__ == "SystemPromptPart":
                            msg_type = "system_prompt"
                        elif part.__class__.__name__ == "UserPromptPart":
                            if skip_user_message and part.content == skip_user_message:
                                continue
                            msg_type = "user_message"
                            if self.first_user_message is None and hasattr(part, "content"):
                                self.first_user_message = part.content
                        else:
                            msg_type = "request_part"

                        message_data = {
                            "timestamp": timestamp,
                            "type": msg_type,
                            "content": part.content,
                            "message_index": self.message_count,
                            "pydantic_type": part.__class__.__name__,
                            "pydantic_data": to_jsonable_python(part),
                        }
                    else:
                        continue

                    self.messages.append(message_data)
                    self.message_count += 1
                    self.last_message_timestamp = timestamp
                    self._log_message_to_history(message_data)

            elif isinstance(msg, ModelResponse):
                for part in msg.parts:
                    if part.__class__.__name__ == "ToolCallPart":
                        message_data = {
                            "timestamp": timestamp,
                            "type": "tool_call",
                            "content": f"Tool call: {getattr(part, 'tool_name', 'unknown')}",
                            "message_index": self.message_count,
                            "pydantic_type": part.__class__.__name__,
                            "pydantic_data": to_jsonable_python(part),
                            "model_name": getattr(msg, "model_name", None),
                            "usage": to_jsonable_python(getattr(msg, "usage", None)) if hasattr(msg, "usage") else None,
                        }
                    elif hasattr(part, "content"):
                        message_data = {
                            "timestamp": timestamp,
                            "type": "assistant_response",
                            "content": part.content,
                            "message_index": self.message_count,
                            "pydantic_type": part.__class__.__name__,
                            "pydantic_data": to_jsonable_python(part),
                            "model_name": getattr(msg, "model_name", None),
                            "usage": to_jsonable_python(getattr(msg, "usage", None)) if hasattr(msg, "usage") else None,
                        }
                    else:
                        continue

                    self.messages.append(message_data)
                    self.message_count += 1
                    self.last_message_timestamp = timestamp
                    self._log_message_to_history(message_data)

        self._update_metadata()

    def get_session_info(self) -> dict[str, Any]:
        return {
            "session_directory": str(self.session_dir),
            "session_timestamp": self.session_timestamp,
            "title": self._session_title or "New Chat",
            "message_count": self.message_count,
            "last_message_timestamp": self.last_message_timestamp,
        }

    def estimate_tokens(self, text: str) -> int:
        encoding = self._get_encoding()
        if encoding is not None:
            return len(encoding.encode(text))
        # Fallback: rough estimate ~4 chars per token
        return len(text) // 4

    def get_total_context_tokens(self) -> int:
        if hasattr(self.session_costs, "total_usage") and self.session_costs.total_usage.total_tokens > 0:
            return self.session_costs.total_usage.total_tokens

        total = 0
        for message in self.messages:
            if isinstance(message.get("content"), str):
                total += self.estimate_tokens(message["content"])

        if self.compressed_context:
            total += self.estimate_tokens(self.compressed_context)

        return total

    def should_compress_context(self) -> bool:
        total_tokens = self.get_total_context_tokens()
        threshold = self.context_window * 0.9
        return total_tokens >= threshold

    async def compress_context_if_needed(self) -> None:
        if not self.should_compress_context():
            return

        from rich.progress import Progress, SpinnerColumn, TextColumn
        from libagentic.agents import get_compression_agent

        recent_preserve_count = 3
        messages_to_compress = (
            self.messages[:-recent_preserve_count] if len(self.messages) > recent_preserve_count else []
        )

        if not messages_to_compress:
            return

        progress = Progress(
            SpinnerColumn(),
            TextColumn("Compressing conversation..."),
            transient=True,
        )

        with progress:
            progress.add_task("", total=None)
            conversation_text = self._format_messages_for_compression(messages_to_compress)
            compression_agent = get_compression_agent()
            result = await compression_agent.run(f"Compress this conversation:\n\n{conversation_text}")
            self.compressed_context = result.output.strip()
            self.messages = self.messages[-recent_preserve_count:]

        self._log_compression_event(len(messages_to_compress))

    def _format_messages_for_compression(self, messages: list[dict]) -> str:
        formatted = []
        for msg in messages:
            role = msg.get("type", "unknown")
            content = msg.get("content", "")
            if role == "user_message":
                formatted.append(f"USER: {content}")
            elif role == "assistant_response":
                formatted.append(f"ASSISTANT: {content}")
            elif role == "system_prompt":
                formatted.append(f"SYSTEM: {content}")
        return "\n\n".join(formatted)

    def _log_compression_event(self, compressed_message_count: int) -> None:
        timestamp = datetime.now(UTC).isoformat()
        compression_data = {
            "timestamp": timestamp,
            "type": "context_compression",
            "content": f"Compressed {compressed_message_count} messages due to context window limit",
            "message_index": self.message_count,
            "metadata": {
                "compressed_messages": compressed_message_count,
                "remaining_messages": len(self.messages),
                "compressed_context_tokens": self.estimate_tokens(self.compressed_context)
                if self.compressed_context
                else 0,
            },
        }
        self.messages.append(compression_data)
        self.message_count += 1
        self.last_message_timestamp = timestamp
        self._log_message_to_history(compression_data)
        self._update_metadata()

    def get_pydantic_message_history(self) -> list:
        try:
            from pydantic_ai.messages import ModelRequest, ModelResponse, TextPart, UserPromptPart, ToolCallPart, ToolReturnPart
        except ImportError:
            return []

        pydantic_messages = []
        current_request_parts = []
        current_response_parts = []

        for message in self.messages:
            msg_type = message.get("type", "unknown")
            pydantic_data = message.get("pydantic_data")

            if msg_type in ["system_prompt", "context_compression"]:
                continue

            if pydantic_data:
                try:
                    pydantic_type = message.get("pydantic_type", "")

                    if pydantic_type == "UserPromptPart":
                        part = UserPromptPart(**pydantic_data)
                        current_request_parts.append(part)
                    elif pydantic_type == "ToolReturnPart":
                        part = ToolReturnPart(**pydantic_data)
                        current_request_parts.append(part)
                    elif pydantic_type == "TextPart":
                        part = TextPart(**pydantic_data)
                        current_response_parts.append(part)
                    elif pydantic_type == "ToolCallPart":
                        part = ToolCallPart(**pydantic_data)
                        current_response_parts.append(part)

                    if pydantic_type in ["UserPromptPart", "ToolReturnPart"]:
                        if current_response_parts:
                            response = ModelResponse(parts=current_response_parts)
                            pydantic_messages.append(response)
                            current_response_parts = []

                    elif pydantic_type in ["TextPart", "ToolCallPart"]:
                        if current_request_parts:
                            request = ModelRequest(parts=current_request_parts)
                            pydantic_messages.append(request)
                            current_request_parts = []

                except Exception:
                    continue
            else:
                content = message.get("content", "")

                if msg_type == "user_message":
                    if current_response_parts:
                        response = ModelResponse(parts=current_response_parts)
                        pydantic_messages.append(response)
                        current_response_parts = []
                    current_request_parts.append(UserPromptPart(content=content))

                elif msg_type == "assistant_response":
                    if current_request_parts:
                        request = ModelRequest(parts=current_request_parts)
                        pydantic_messages.append(request)
                        current_request_parts = []
                    current_response_parts.append(TextPart(content=content))

        if current_request_parts:
            request = ModelRequest(parts=current_request_parts)
            pydantic_messages.append(request)
        if current_response_parts:
            response = ModelResponse(parts=current_response_parts)
            pydantic_messages.append(response)

        return pydantic_messages

    def get_conversation_context(self) -> list[dict]:
        return self.messages


class SessionLister:
    """Handles scanning and displaying past chat sessions for resumption."""

    def __init__(self, app_name: str = "chatinterface"):
        self.app_name = app_name
        self.sessions_dir = Path.home() / f".{app_name}" / "sessions"

    def get_available_sessions(self) -> list[dict[str, Any]]:
        sessions = []
        if not self.sessions_dir.exists():
            return sessions

        for session_dir in self.sessions_dir.iterdir():
            if not session_dir.is_dir():
                continue
            metadata_file = session_dir / "metadata.json"
            if not metadata_file.exists():
                continue
            try:
                with metadata_file.open("r", encoding="utf-8") as f:
                    metadata = json.load(f)
                metadata["session_dir"] = str(session_dir)
                metadata["session_timestamp"] = session_dir.name
                sessions.append(metadata)
            except (json.JSONDecodeError, OSError):
                continue

        sessions.sort(key=lambda s: s.get("created_timestamp", ""), reverse=True)
        return sessions

    def format_session_display(self, session: dict[str, Any]) -> str:
        title = session.get("title", "Untitled Session")
        created_timestamp = session.get("created_timestamp", "")
        message_count = session.get("message_count", 0)

        try:
            created_dt = datetime.fromisoformat(created_timestamp.replace("Z", "+00:00"))
            now = datetime.now(created_dt.tzinfo)
            time_diff = now - created_dt

            if time_diff.days > 0:
                time_str = "1 day ago" if time_diff.days == 1 else f"{time_diff.days} days ago"
            elif time_diff.seconds > 3600:
                hours = time_diff.seconds // 3600
                time_str = f"{hours} hour{'s' if hours != 1 else ''} ago"
            elif time_diff.seconds > 60:
                minutes = time_diff.seconds // 60
                time_str = f"{minutes} minute{'s' if minutes != 1 else ''} ago"
            else:
                time_str = "Just now"
        except (ValueError, AttributeError):
            time_str = "Unknown time"

        return f"{title:<50} ({time_str}, {message_count} message{'s' if message_count != 1 else ''})"

    def show_session_selection(self, console: Console) -> str | None:
        sessions = self.get_available_sessions()

        if not sessions:
            console.print("[yellow]No previous sessions found.[/yellow]")
            return None

        console.print()
        console.print("[bold blue]Resume Session[/bold blue]")
        console.print("[dim]Select a session to resume:[/dim]")
        console.print()

        for i, session in enumerate(sessions, 1):
            display_text = self.format_session_display(session)
            console.print(f"[bold cyan]{i}.[/bold cyan] {display_text}")

        console.print()
        console.print(f"[dim]Enter session number (1-{len(sessions)}) or press Enter to cancel:[/dim]")

        try:
            choice = console.input("[bold green]Select session: [/bold green]").strip()

            if not choice:
                return None

            session_num = int(choice)
            if 1 <= session_num <= len(sessions):
                return sessions[session_num - 1]["session_dir"]
            else:
                console.print(f"[red]Invalid selection. Please choose 1-{len(sessions)}[/red]")
                return None

        except (ValueError, KeyboardInterrupt):
            return None


class ResumableSessionManager(SessionManager):
    """Extended SessionManager that can load from existing sessions."""

    @classmethod
    def from_existing_session(
        cls, session_dir: str, app_name: str = "chatinterface", context_window: int | None = None
    ) -> "ResumableSessionManager":
        session_path = Path(session_dir)
        if not session_path.exists():
            raise ValueError(f"Session directory does not exist: {session_dir}")

        metadata_file = session_path / "metadata.json"
        history_file = session_path / "history.jsonl"

        if not metadata_file.exists() or not history_file.exists():
            raise ValueError(f"Invalid session directory (missing metadata or history): {session_dir}")

        instance = cls.__new__(cls)

        if context_window is None:
            context_window = int(os.getenv("CONTEXT_WINDOW", "200000"))

        instance.app_name = app_name
        instance.sessions_dir = session_path.parent
        instance.session_id = session_path.name
        instance.session_timestamp = session_path.name
        instance.session_dir = session_path
        instance.metadata_file = metadata_file
        instance.history_file = history_file

        try:
            with metadata_file.open("r", encoding="utf-8") as f:
                metadata = json.load(f)
            instance._session_title = metadata.get("title", "Resumed Session")
            instance._title_generated = True
            instance.message_count = metadata.get("message_count", 0)
            instance.last_message_timestamp = metadata.get("last_message_timestamp")
        except (json.JSONDecodeError, OSError):
            instance._session_title = "Resumed Session"
            instance._title_generated = True
            instance.message_count = 0
            instance.last_message_timestamp = None

        instance.first_user_message = None
        instance.messages = []
        instance.session_costs = SessionCosts()

        try:
            with metadata_file.open("r", encoding="utf-8") as f:
                metadata = json.load(f)
                usage_data = metadata.get("usage", {})

                if usage_data:
                    from pydantic_ai.usage import RunUsage

                    if "total" in usage_data:
                        total_data = usage_data["total"]
                        input_tokens = total_data.get("input_tokens", 0)
                        output_tokens = total_data.get("output_tokens", 0)
                        total_tokens = total_data.get("total_tokens", 0)
                        requests = total_data.get("requests", 0)
                        cache_read_tokens = total_data.get("cached_tokens", 0)
                    else:
                        total_tokens = usage_data.get("total_tokens", 0)
                        input_tokens = usage_data.get("input_tokens", 0)
                        output_tokens = usage_data.get("output_tokens", 0)
                        requests = usage_data.get("requests", 1 if total_tokens > 0 else 0)
                        cache_read_tokens = usage_data.get("cached_tokens", 0)

                        if total_tokens > 0 and input_tokens == 0 and output_tokens == 0:
                            input_tokens = int(total_tokens * 0.7)
                            output_tokens = total_tokens - input_tokens

                    if total_tokens > 0 or input_tokens > 0 or output_tokens > 0:
                        restored_usage = RunUsage(
                            input_tokens=input_tokens,
                            output_tokens=output_tokens,
                            requests=requests,
                            cache_read_tokens=cache_read_tokens,
                        )
                        usage_costs = calculate_usage_cost(restored_usage, None)
                        add_usage_to_session(instance.session_costs, usage_costs)

        except (json.JSONDecodeError, OSError, ImportError, TypeError):
            pass

        instance.context_window = context_window
        instance.compressed_context = None
        instance._encoding = None

        instance._load_message_history()

        return instance

    def _load_message_history(self) -> None:
        try:
            with self.history_file.open("r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            message_data = json.loads(line)
                            self.messages.append(message_data)
                            msg_index = message_data.get("message_index", 0)
                            if msg_index >= self.message_count:
                                self.message_count = msg_index + 1
                        except json.JSONDecodeError:
                            continue
        except (OSError, FileNotFoundError):
            pass
