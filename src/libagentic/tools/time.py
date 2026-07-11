"""Time-related tools for agents."""

from datetime import UTC, datetime


def current_datetime() -> str:
    """Get the current date and time in UTC in ISO 8601 format.

    Returns:
        The current datetime as an ISO 8601 string
    """
    return datetime.now(tz=UTC).isoformat()
