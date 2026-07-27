# Contributing to Chief-AI

Thank you for considering contributing to Chief-AI! Here's how to get started.

## Getting Started

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/Chief-AI.git`
3. **Create** a branch: `git checkout -b feature/amazing-feature`
4. **Install** dependencies: `uv sync`
5. **Make** your changes
6. **Test**: `uv run pytest`
7. **Commit**: `git commit -m "feat: add amazing feature"`
8. **Push**: `git push origin feature/amazing-feature`
9. **Open** a Pull Request

## Development Setup

```bash
# Clone and install
git clone https://github.com/YogendraChukka01/Chief-AI.git
cd Chief-AI
uv sync

# Run tests
uv run pytest

# Lint
uv run ruff check .
uv run ruff format .
```

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/):

- `feat:` — New feature
- `fix:` — Bug fix
- `docs:` — Documentation changes
- `style:` — Code style changes
- `refactor:` — Code refactoring
- `test:` — Adding tests
- `chore:` — Maintenance tasks

## Code Style

- Follow PEP 8 (enforced by ruff)
- Add type hints to all functions
- Write docstrings for public APIs
- Keep functions focused and small

## Pull Request Guidelines

- Fill out the PR template
- Link related issues
- Add screenshots for UI changes
- Ensure CI passes
- Request review from maintainers
