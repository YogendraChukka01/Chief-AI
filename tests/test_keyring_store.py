"""Tests for keyring store (requires keyring backend)."""

import pytest

from libagentic.keyring_store import (
    API_KEY_NAMES,
    delete_api_key,
    get_all_api_keys,
    get_api_key,
    has_api_key,
    store_api_key,
)


@pytest.mark.skipif(
    not _keyring_available(),
    reason="Keyring backend not available in test environment",
)
class TestKeyringStore:
    """Tests for keyring operations."""

    def test_store_and_retrieve(self) -> None:
        """Should store and retrieve an API key."""
        test_key = "test_key_store"
        test_value = "test-value-12345"

        store_api_key(test_key, test_value)
        retrieved = get_api_key(test_key)

        assert retrieved == test_value

        # Cleanup
        delete_api_key(test_key)

    def test_get_nonexistent_returns_none(self) -> None:
        """Should return None for non-existent key."""
        result = get_api_key("nonexistent_key_12345")
        assert result is None

    def test_has_key(self) -> None:
        """Should correctly report key existence."""
        test_key = "test_key_exists"
        test_value = "exists"

        store_api_key(test_key, test_value)
        assert has_api_key(test_key) is True

        delete_api_key(test_key)
        assert has_api_key(test_key) is False

    def test_delete_nonexistent_returns_false(self) -> None:
        """Should return False when deleting non-existent key."""
        result = delete_api_key("nonexistent_key_12345")
        assert result is False

    def test_get_all_keys(self) -> None:
        """Should return dictionary of all API keys."""
        result = get_all_api_keys()
        assert isinstance(result, dict)
        assert len(result) == len(API_KEY_NAMES)


def _keyring_available() -> bool:
    """Check if keyring backend is available."""
    try:
        import keyring

        keyring.set_password("test-backend-check", "test", "test")
        keyring.delete_password("test-backend-check", "test")
        return True
    except Exception:
        return False
