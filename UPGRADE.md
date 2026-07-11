# Upgrade Guide: chief-ai v0.1.6 → v0.2.0

## Overview

This upgrade introduces production-grade improvements based on 2026 best practices research.

## Key Changes

### 1. Centralized Model Configuration

**Before:** Model names scattered across 4+ files

**After:** Single source of truth in `src/libagentic/models_config.py`

```python
# New centralized config
from libagentic.models_config import ANTHROPIC_CLAUDE_SONNET_4, calculate_cost

# Cost calculation
cost = calculate_cost(input_tokens=1000, output_tokens=500, model=ANTHROPIC_CLAUDE_SONNET_4)
```

### 2. Secure API Key Storage

**Before:** Plaintext JSON in `~/.chen/settings.json`

**After:** OS keychain integration via `keyring` library

```python
from libagentic.keyring_store import store_api_key, get_api_key

# Keys stored in OS keychain (macOS Keychain, Windows Credential Locker)
store_api_key("anthropic_api_key", "sk-ant-...")
api_key = get_api_key("anthropic_api_key")
```

**Migration:** Existing settings files will automatically migrate secrets to keychain on first run.

### 3. Structured Logging

**Before:** `except Exception: pass` throughout codebase

**After:** Proper logging with `libagentic.logging` module

```python
from libagentic.logging import get_logger, setup_logger

logger = get_logger("my-module")
logger.info("Operation completed")
logger.exception("Error occurred")
```

### 4. Improved Type Annotations

**Before:** Misleading type hints
```python
def get_chief_agent(mcps: list[MCPServer] = None)  # Wrong: claims list, actually None
```

**After:** Correct Optional types
```python
def get_chief_agent(mcps: list[MCPServer] | None = None)  # Correct
```

### 5. Provider Selection Simplified

**Before:** Complex match/case with 8 branches

**After:** Dynamic provider list construction
```python
available_providers = []
if anthropic_api_key:
    available_providers.append(get_anthropic_model(...))
# ...
return FallbackModel(*available_providers)
```

### 6. Testing Infrastructure

**Before:** Zero tests

**After:** Comprehensive test suite with fixtures

```bash
# Run tests
uv run pytest tests/ -v

# With coverage
uv run pytest tests/ --cov=src --cov-report=term-missing
```

**Test files:**
- `tests/test_models_config.py` - Model configuration tests
- `tests/test_providers.py` - Provider creation tests
- `tests/test_logging.py` - Logging configuration tests
- `tests/test_keyring_store.py` - Keychain integration tests

### 7. CI/CD Pipeline

**Before:** No CI

**After:** GitHub Actions with lint, typecheck, and test jobs

```yaml
# .github/workflows/ci.yml
- Lint (ruff)
- Type check
- Tests (Python 3.12 + 3.13)
```

### 8. pyproject.toml Updates

- Added `keyring>=25.0.0` for secure storage
- Added `rich>=14.0.0` explicitly
- Added `[project.optional-dependencies]` for dev tools
- Added mypy and pytest configurations
- Updated Python requirement to `>=3.12`

## Migration Steps

1. **Update dependencies:**
   ```bash
   uv lock --upgrade
   uv sync
   ```

2. **First run will migrate secrets:**
   - Existing JSON settings will be read
   - API keys will be moved to OS keychain
   - JSON file will store `null` for secret fields

3. **Run tests to verify:**
   ```bash
   uv run pytest tests/ -v
   ```

## New File Structure

```
src/
├── libagentic/
│   ├── __init__.py
│   ├── agents.py          # Agent factories (updated)
│   ├── keyring_store.py   # NEW: Secure keychain storage
│   ├── logging.py         # NEW: Structured logging
│   ├── models.py          # Dependencies
│   ├── models_config.py   # NEW: Centralized model config
│   ├── prompts.py         # System prompts (unchanged)
│   ├── providers.py       # Provider config (simplified)
│   └── tools/
├── appclis/
│   ├── __init__.py
│   ├── chen.py            # Updated with logging
│   ├── chief.py           # Updated with logging
│   └── settings/
│       ├── __init__.py
│       ├── chen_settings.py
│       └── settings_manager.py  # Updated with keyring
├── libchatinterface/      # (unchanged)
└── libshared/             # (unchanged)
tests/
├── conftest.py            # NEW: Test fixtures
├── test_models_config.py  # NEW
├── test_providers.py      # NEW
├── test_logging.py        # NEW
└── test_keyring_store.py  # NEW
.github/
└── workflows/
    └── ci.yml             # NEW: CI pipeline
```

## Breaking Changes

- None. All existing functionality preserved.

## Dependencies Added

- `keyring>=25.0.0` - OS keychain integration
- `rich>=14.0.0` - Terminal formatting (was implicit via Typer)

## Next Steps

1. Add integration tests with mocked LLM calls
2. Implement session persistence (currently marked as not implemented)
3. Add MCP server support
4. Add `py.typed` marker for PEP 561 compliance
5. Consider adding `mypy --strict` to CI
