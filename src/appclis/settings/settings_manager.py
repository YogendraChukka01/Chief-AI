"""Settings management with JSON file storage and OS keychain integration."""

import json
import os
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.prompt import Confirm, Prompt
from rich.table import Table

from appclis.settings.chen_settings import ChenSettings
from libagentic.keyring_store import (
    API_KEY_NAMES,
    clear_all_api_keys,
    get_all_api_keys,
    get_api_key,
    store_all_api_keys,
)
from libagentic.logging import get_logger

logger = get_logger("settings")
console = Console()

MAX_RETRIES = 3


class SettingsManager:
    """Manages settings with JSON file storage and secure keychain integration."""

    def __init__(self, settings_dir: Path | None = None) -> None:
        """Initialize the settings manager.

        Args:
            settings_dir: Custom directory for settings. Defaults to ~/.chen/
        """
        self.settings_dir = settings_dir or Path.home() / ".chen"
        self.settings_file = self.settings_dir / "settings.json"

    def ensure_settings_dir(self) -> None:
        """Create the settings directory if it doesn't exist."""
        self.settings_dir.mkdir(parents=True, exist_ok=True)
        if os.name != "nt":
            os.chmod(self.settings_dir, 0o700)

    def settings_exist(self) -> bool:
        """Check if settings file exists."""
        return self.settings_file.exists()

    def load_settings(self) -> ChenSettings:
        """Load settings from JSON file, trigger onboarding if needed.

        Returns:
            ChenSettings: The loaded or newly created settings
        """
        if not self.settings_exist():
            return self._run_onboarding()

        try:
            with self.settings_file.open(encoding="utf-8") as f:
                data = json.load(f)

            # Merge with keychain secrets
            keychain_keys = get_all_api_keys()
            for key, value in keychain_keys.items():
                if value and not data.get(key):
                    data[key] = value

            return ChenSettings.model_validate(data)

        except json.JSONDecodeError as e:
            logger.error("Invalid JSON in settings file: %s", e)
            console.print(f"[red]Error loading settings: {e}[/red]")
            console.print("[yellow]Running onboarding to recreate settings...[/yellow]")
            return self._run_onboarding()

        except ValueError as e:
            # Pydantic validation error (e.g., missing API keys)
            logger.warning("Settings validation failed: %s", e)
            console.print(f"[yellow]Settings validation: {e}[/yellow]")
            console.print("[yellow]Running onboarding...[/yellow]")
            return self._run_onboarding()

        except Exception as e:
            logger.exception("Unexpected error loading settings")
            console.print(f"[red]Error loading settings: {e}[/red]")
            return self._run_onboarding()

    def save_settings(self, settings: ChenSettings) -> None:
        """Save settings to JSON file and keychain for secrets.

        Args:
            settings: The settings to save
        """
        self.ensure_settings_dir()

        settings_dict = settings.model_dump()
        secrets = {}
        non_secrets = {}

        for key, value in settings_dict.items():
            if key in API_KEY_NAMES and value:
                secrets[key] = value
                # Don't include secrets in JSON at all
            else:
                non_secrets[key] = value

        # Store secrets in keychain
        if secrets:
            stored = store_all_api_keys(secrets)
            logger.info("Stored %d secrets in OS keychain", stored)

        # Store non-secrets in JSON
        with self.settings_file.open("w", encoding="utf-8") as f:
            json.dump(non_secrets, f, indent=2, ensure_ascii=False)

        if os.name != "nt":
            os.chmod(self.settings_file, 0o600)

        console.print(f"[green]Settings saved to {self.settings_file}[/green]")
        if secrets:
            console.print("[dim]Secrets stored securely in OS keychain[/dim]")

    def _run_onboarding(self) -> ChenSettings:
        """Run the interactive onboarding process to collect settings.

        Returns:
            ChenSettings: The configured settings
        """
        console.print("\n[bold blue]Welcome to Chen![/bold blue]")
        console.print("Let's configure your settings. Press Enter to skip optional fields.\n")

        env_defaults = self._get_env_defaults()
        keychain_keys = get_all_api_keys()

        for key in API_KEY_NAMES:
            if keychain_keys.get(key) and not env_defaults.get(key):
                env_defaults[key] = keychain_keys[key]

        if env_defaults:
            console.print("[dim]Found these values in environment:[/dim]")
            table = Table(show_header=False, box=None)
            for key, value in env_defaults.items():
                if value:
                    display_value = value if not key.endswith("_key") else f"{value[:8]}..."
                    table.add_row(f"  {key}:", f"[dim]{display_value}[/dim]")
            console.print(table)
            console.print()

        settings_data: dict[str, Any] = {}

        # API Keys
        for key_name, display_name, url in [
            ("anthropic_api_key", "Anthropic API key", "https://console.anthropic.com/settings/keys"),
            ("openai_api_key", "OpenAI API key", "https://platform.openai.com/api-keys"),
            ("openrouter_api_key", "OpenRouter API key", "https://openrouter.ai/settings/keys"),
            ("tavily_api_key", "Tavily API key (web search)", "https://app.tavily.com/home"),
        ]:
            value = self._prompt_for_setting(
                key_name,
                f"Your {display_name}",
                url,
                env_defaults.get(key_name),
                mask_input=True,
            )
            if value:
                settings_data[key_name] = value

        # Language
        language = self._prompt_for_setting(
            "language",
            "Preferred language (e.g., English, Bahasa Indonesia)",
            None,
            env_defaults.get("language", "English"),
        )
        if language:
            settings_data["language"] = language

        # Context Window
        context_window = self._prompt_for_setting(
            "context_window",
            "Context window size (tokens)",
            None,
            str(env_defaults.get("context_window", 200000)),
            field_type=int,
        )
        if context_window:
            settings_data["context_window"] = context_window

        try:
            settings = ChenSettings.model_validate(settings_data)
            self.save_settings(settings)

            console.print("\n[green]Configuration complete![/green]")
            console.print(f"Settings saved to: [dim]{self.settings_file}[/dim]\n")

            return settings

        except Exception as e:
            logger.exception("Configuration validation failed")
            console.print(f"\n[red]Configuration failed: {e}[/red]")
            console.print("Please check your API keys and try again.")
            raise

    def _get_env_defaults(self) -> dict[str, Any]:
        """Get default values from environment variables.

        Returns:
            Dict with environment variable values
        """
        context_window_str = os.environ.get("CONTEXT_WINDOW", "200000")
        try:
            context_window = int(context_window_str)
        except ValueError:
            logger.warning("Invalid CONTEXT_WINDOW value: %s, using default", context_window_str)
            context_window = 200000

        return {
            "anthropic_api_key": os.environ.get("ANTHROPIC_API_KEY"),
            "openai_api_key": os.environ.get("OPENAI_API_KEY"),
            "openrouter_api_key": os.environ.get("OPENROUTER_API_KEY"),
            "tavily_api_key": os.environ.get("TAVILY_API_KEY"),
            "language": os.environ.get("LANGUAGE"),
            "context_window": context_window,
        }

    def _prompt_for_setting(
        self,
        field_name: str,
        display_name: str,
        url_hint: str | None = None,
        default: Any | None = None,
        mask_input: bool = False,
        field_type: type = str,
    ) -> Any | None:
        """Prompt user for a setting value with retry limit.

        Args:
            field_name: The field name in settings
            display_name: Human readable name for the field
            url_hint: URL where user can get the value
            default: Default value to use
            mask_input: Whether to mask the input
            field_type: Type to convert the input to

        Returns:
            The entered value or None if skipped
        """
        prompt_text = f"[bold]{display_name}[/bold]"
        if url_hint:
            prompt_text += f" [dim]({url_hint})[/dim]"

        if default:
            display_default = f"{str(default)[:8]}..." if mask_input and len(str(default)) > 8 else str(default)
            prompt_text += f" [dim](default: {display_default})[/dim]"

        prompt_text += ": "

        for attempt in range(MAX_RETRIES):
            try:
                if mask_input:
                    value = Prompt.ask(prompt_text, password=True, default=str(default) if default else "")
                else:
                    value = Prompt.ask(prompt_text, default=str(default) if default else "")

                if not value.strip():
                    return None

                if field_type is int:
                    return int(value)
                return value

            except (KeyboardInterrupt, EOFError):
                console.print("\n[yellow]Onboarding cancelled[/yellow]")
                raise

            except ValueError as e:
                remaining = MAX_RETRIES - attempt - 1
                if remaining > 0:
                    console.print(f"[red]Invalid value: {e} ({remaining} attempts remaining)[/red]")
                else:
                    console.print(f"[red]Invalid value: {e}. No attempts remaining.[/red]")
                    return None

        return None

    def show_current_settings(self) -> None:
        """Display current settings in a formatted table."""
        if not self.settings_exist():
            console.print("[yellow]No settings file found. Run chen to trigger onboarding.[/yellow]")
            return

        try:
            settings = self.load_settings()

            console.print(f"\n[bold]Chen Settings[/bold] [dim]({self.settings_file})[/dim]\n")

            table = Table(show_header=True, header_style="bold blue")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            table.add_column("Status", justify="center")

            for field_name, field_info in settings.model_fields.items():
                value = getattr(settings, field_name)

                if value is None:
                    display_value = "[dim]Not set[/dim]"
                    status = "[red]X[/red]"
                elif field_name.endswith("_api_key"):
                    display_value = f"{str(value)[:8]}..." if len(str(value)) > 8 else str(value)
                    status = "[green]OK[/green]"
                else:
                    display_value = str(value)
                    status = "[green]OK[/green]"

                description = field_info.description or field_name
                table.add_row(description, display_value, status)

            console.print(table)
            console.print()

        except Exception as e:
            logger.exception("Error reading settings")
            console.print(f"[red]Error reading settings: {e}[/red]")

    def get_setting(self, key: str) -> Any:
        """Get a single setting value.

        Args:
            key: The setting key to retrieve

        Returns:
            The setting value

        Raises:
            ValueError: If key doesn't exist
        """
        if not self.settings_exist():
            console.print("[yellow]No settings file found. Run chen to trigger onboarding.[/yellow]")
            return None

        valid_keys = list(ChenSettings.model_fields.keys())
        if key not in valid_keys:
            raise ValueError(f"Invalid setting key '{key}'. Valid keys: {', '.join(valid_keys)}")

        settings = self.load_settings()
        return getattr(settings, key)

    def set_setting(self, key: str, value: str) -> None:
        """Set a single setting value.

        Args:
            key: The setting key to set
            value: The string value to set

        Raises:
            ValueError: If key doesn't exist or value is invalid
        """
        if not self.settings_exist():
            console.print("[yellow]No settings file found. Run onboarding first.[/yellow]")
            return

        valid_keys = list(ChenSettings.model_fields.keys())
        if key not in valid_keys:
            raise ValueError(f"Invalid setting key '{key}'. Valid keys: {', '.join(valid_keys)}")

        settings = self.load_settings()
        settings_dict = settings.model_dump()

        converted_value = self._convert_setting_value(key, value)
        settings_dict[key] = converted_value

        try:
            updated_settings = ChenSettings.model_validate(settings_dict)
            self.save_settings(updated_settings)
            console.print(f"[green]Setting '{key}' updated successfully[/green]")
        except Exception as e:
            raise ValueError(f"Failed to update setting: {e}") from e

    def _convert_setting_value(self, key: str, value: str) -> Any:
        """Convert string value to the correct type for the given setting key.

        Args:
            key: The setting key
            value: The string value to convert

        Returns:
            The converted value
        """
        field_info = ChenSettings.model_fields[key]

        if not value or value.lower() in ("none", "null", ""):
            return None

        field_type = field_info.annotation

        if hasattr(field_type, "__args__"):
            args = field_type.__args__
            field_type = next((arg for arg in args if arg is not type(None)), str)

        if field_type is int:
            try:
                converted = int(value)
                # Check gt constraint if present
                metadata = field_info.metadata if hasattr(field_info, "metadata") else []
                for constraint in metadata:
                    if hasattr(constraint, "gt") and constraint.gt is not None:
                        if converted <= constraint.gt:
                            raise ValueError(f"Value must be greater than {constraint.gt}")
                return converted
            except ValueError as e:
                raise ValueError(f"Invalid integer value '{value}' for {key}: {e}") from e

        return value

    def reset_settings(self) -> bool:
        """Reset settings by deleting the settings file and clearing keychain.

        Returns:
            True if settings were reset, False if cancelled
        """
        if not self.settings_exist():
            console.print("[yellow]No settings file exists to reset.[/yellow]")
            return False

        if not Confirm.ask(
            f"Are you sure you want to reset all settings?\n"
            f"This will delete {self.settings_file} and all stored API keys."
        ):
            console.print("[yellow]Reset cancelled.[/yellow]")
            return False

        try:
            # Delete JSON file
            self.settings_file.unlink()

            # Clear keychain secrets
            cleared = clear_all_api_keys()
            if cleared:
                console.print(f"[dim]Cleared {cleared} API keys from OS keychain[/dim]")

            console.print("[green]Settings reset successfully.[/green]")
            console.print("Run chen again to trigger onboarding.")
            return True

        except Exception as e:
            logger.exception("Error resetting settings")
            console.print(f"[red]Error resetting settings: {e}[/red]")
            return False
