from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from stac_mcp.tools.client import STACClient
from stac_mcp.tools.execution import Session


def test_stac_client_init():
    """Verify STACClient initialization."""
    client = STACClient()
    assert client.catalog_url is not None


def test_stac_client_session_dependency():
    """Verify that the STAC client is correctly injected into the session."""
    session = Session(client=MagicMock())
    stac_client = session.stac_client
    assert isinstance(stac_client, STACClient)


def test_list_collection_keywords():
    """Test list_collection_keywords returns keywords or description fallback."""
    col_with_kw = SimpleNamespace(
        id="col-a", keywords=["climate", "temperature"], description="Full desc.", title="Col A"
    )
    col_with_desc = SimpleNamespace(
        id="col-b", keywords=None, description="Ocean color data. More details.", title="Col B"
    )
    col_bare = SimpleNamespace(
        id="col-c", keywords=None, description=None, title="Col C"
    )

    client = STACClient()
    client._client = MagicMock()  # noqa: SLF001
    client._client.get_collections.return_value = [col_with_kw, col_with_desc, col_bare]

    result = client.list_collection_keywords()
    assert result["col-a"] == ["climate", "temperature"]
    assert result["col-b"] == "Ocean color data"
    assert result["col-c"] == "Col C"
