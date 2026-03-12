import pytest
from fastmcp.client import Client

from stac_mcp.server import app


@pytest.fixture
def test_app():
    """Return a clean app for each test."""
    original_components = app._local_provider._components.copy()  # noqa: SLF001
    yield app
    app._local_provider._components = original_components  # noqa: SLF001


@pytest.mark.asyncio
async def test_get_prompt_returns_promptmessage_and_machine_payload(test_app):
    """Ensure get_prompt returns messages with human text and meta payload."""
    client = Client(test_app)
    async with client:
        result = await client.get_prompt("tool_get_root_prompt")

    assert hasattr(result, "messages")
    assert isinstance(result.messages, list), (
        "get_prompt() should return a list of messages"
    )
    assert len(result.messages) > 0, "get_prompt() returned an empty list of messages"

    msg = result.messages[0]
    assert hasattr(msg, "content"), "Message should have .content"
    assert hasattr(msg.content, "text"), "Message.content should have .text"
    assert isinstance(msg.content.text, str), (
        "Message.content.text should be a string"
    )

    # In FastMCP 3.x, meta is on the PromptResult, not individual messages
    result_meta = getattr(result, "meta", None)
    assert result_meta is not None, "PromptResult should expose meta"
    assert "machine_payload" in result_meta, (
        "machine_payload should be present in meta"
    )
    payload = result_meta["machine_payload"]
    assert isinstance(payload, dict)
    assert payload.get("name") == "get_root"
