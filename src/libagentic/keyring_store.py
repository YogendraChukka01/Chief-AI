"""Secure API key storage using OS keychain."""

import logging

import keyring
import keyring.errors

logger = logging.getLogger("chief-ai.keyring")

SERVICE_NAME = "chief-ai"


def store_api_key(key_name: str, value: str) -> bool:
    """Store an API key in the OS keychain.

    Args:
        key_name: Identifier for the key (e.g., 'anthropic_api_key')
        value: The API key value to store

    Returns:
        True if stored successfully, False otherwise
    """
    if not key_name or not value:
        logger.warning("Attempted to store empty key name or value")
        return False

    try:
        keyring.set_password(SERVICE_NAME, key_name, value)
        logger.debug("Stored key '%s' in OS keychain", key_name)
        return True
    except keyring.errors.PasswordSetError as e:
        logger.error("Failed to store key '%s': %s", key_name, e)
        return False
    except Exception as e:
        logger.error("Unexpected error storing key '%s': %s", key_name, e)
        return False


def get_api_key(key_name: str) -> str | None:
    """Retrieve an API key from the OS keychain.

    Args:
        key_name: Identifier for the key

    Returns:
        The API key if found, None otherwise
    """
    if not key_name:
        return None

    try:
        return keyring.get_password(SERVICE_NAME, key_name)
    except keyring.errors.PasswordGetError as e:
        logger.error("Failed to retrieve key '%s': %s", key_name, e)
        return None
    except Exception as e:
        logger.error("Unexpected error retrieving key '%s': %s", key_name, e)
        return None


def delete_api_key(key_name: str) -> bool:
    """Delete an API key from the OS keychain.

    Args:
        key_name: Identifier for the key

    Returns:
        True if deleted, False if not found or error
    """
    if not key_name:
        return False

    try:
        keyring.delete_password(SERVICE_NAME, key_name)
        logger.debug("Deleted key '%s' from OS keychain", key_name)
        return True
    except keyring.errors.PasswordDeleteError:
        return False
    except Exception as e:
        logger.error("Unexpected error deleting key '%s': %s", key_name, e)
        return False


def has_api_key(key_name: str) -> bool:
    """Check if an API key exists in the OS keychain.

    Args:
        key_name: Identifier for the key

    Returns:
        True if key exists and is non-empty
    """
    if not key_name:
        return False

    value = get_api_key(key_name)
    return value is not None and value != ""


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


def store_all_api_keys(keys: dict[str, str]) -> int:
    """Store multiple API keys at once.

    Args:
        keys: Dictionary mapping key names to values

    Returns:
        Number of keys successfully stored
    """
    stored = 0
    for name, value in keys.items():
        if name in API_KEY_NAMES and value:
            if store_api_key(name, value):
                stored += 1
    return stored


def clear_all_api_keys() -> int:
    """Delete all API keys from the keychain.

    Returns:
        Number of keys successfully deleted
    """
    deleted = 0
    for name in API_KEY_NAMES:
        if delete_api_key(name):
            deleted += 1
    return deleted
