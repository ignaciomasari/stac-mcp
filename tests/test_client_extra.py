"""Extra tests for stac_mcp/tools/client.py."""

from unittest.mock import MagicMock, patch

import pytest

from stac_mcp.tools.client import STACClient


@pytest.fixture
def client():
    """Fixture for STACClient."""
    with patch("pystac_client.Client.open", return_value=MagicMock()):
        c = STACClient(catalog_url="https://example.com")
        c._search_cache = {}  # noqa: SLF001
        c.headers = {}
        yield c


def test_client_init_with_defaults():
    """Test STACClient.__init__ with default values."""
    with patch("pystac_client.Client.open", return_value=MagicMock()):
        client = STACClient()
        assert (
            client.catalog_url == "https://planetarycomputer.microsoft.com/api/stac/v1"
        )
        assert client.headers == {}


def test_client_init_with_env_var(monkeypatch):
    """Test STACClient respects STAC_API_URL env var."""
    monkeypatch.setenv("STAC_API_URL", "https://custom-stac.example.com/v1")
    with patch("pystac_client.Client.open", return_value=MagicMock()):
        client = STACClient()
        assert client.catalog_url == "https://custom-stac.example.com/v1"


def test_search_cache_key(client: STACClient):
    """Test _search_cache_key."""
    key = client._search_cache_key(  # noqa: SLF001
        collections=["test"],
        bbox=[0, 0, 1, 1],
        datetime="2022-01-01T00:00:00Z",
        query={"key": "value"},
        limit=10,
    )
    assert isinstance(key, str)
