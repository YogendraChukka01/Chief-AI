"""Runtime configuration for Chief AI.

Model selection flows through here so the registry and the opencode generator
share one source for the default model. Per-agent overrides set on
:class:`chief_ai.core.types.SubAgent` always win over this default.
"""

from __future__ import annotations

import os


def default_model() -> str | None:
    """Return the default model from ``CHIEF_MODEL``, or ``None`` to let opencode decide."""
    return os.environ.get("CHIEF_MODEL")
