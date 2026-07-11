"""Secure API key storage using OS keychain."""

import keyring

SERVICE_NAME = "chief-ai"


def store_api_key(key_name: str, value: str) -> None:
    """Store an API key in the OS keychain.

    Args:
        key_name: Identifier for the key (e.g., 'anthropic_api_key')
        value: The API key value to store
    """
    keyring.set_password(SERVICE_NAME, key_name, value)


def get_api_key(key_name: str) -> str | None:
    """Retrieve an API key from the OS keychain.

    Args:
        key_name: Identifier for the key

    Returns:
        The API key if found, None otherwise
    """
    return keyring.get_password(SERVICE_NAME, key_name)


def delete_api_key(key_name: str) -> bool:
    """Delete an API key from the OS keychain.

    Args:
        key_name: Identifier for the key

    Returns:
        True if deleted, False if not found
    """
    try:
        keyring.delete_password(SERVICE_NAME, key_name)
        return True
    except keyring.errors.PasswordDeleteError:
        return False


def has_api_key(key_name: str) -> bool:
    """Check if an API key exists in the OS keychain.

    Args:
        key_name: Identifier for the key

    Returns:
        True if key exists
    """
    return keyring.get_password(SERVICE_NAME, key_name) is not None


API_KEY_NAMES = [
    "anthropic_api_key",
    "openai_api_key",
    "openrouter_api_key",
    "tavily_api_key",
]


def get_all_api_keys() -> dict[str, str | None]:
    """Retrieve all API keys from the keychain.

    Returns:
        Dictionary mapping key names to their values
    """
    return {name: get_api_key(name) for name in API_KEY_NAMES}


def store_all_api_keys(keys: dict[str, str]) -> None:
    """Store multiple API keys at once.

    Args:
        keys: Dictionary mapping key names to values
    """
    for name, value in keys.items():
        if name in API_KEY_NAMES and value:
            store_api_key(name, value)
