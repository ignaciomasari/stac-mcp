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
async def test_get_prompt_messages_include_machine_payload_for_all_prompts(test_app):
    """For each registered prompt, get_prompt() returns a PromptResult with
    `meta['machine_payload']` available so agents may call tools programmatically.
    """
    client = Client(test_app)
    async with client:
        prompts = await client.list_prompts()

        names = [getattr(p, "name", None) for p in prompts]

        assert len(names) > 0

        for name in names:
            if not name:
                continue
            result = await client.get_prompt(name)
            assert hasattr(result, "messages"), f"get_prompt({name}) missing .messages"
            assert len(result.messages) > 0, (
                f"get_prompt({name}) returned empty .messages"
            )
            # In FastMCP 3.x, meta is on the PromptResult, not individual messages
            result_meta = getattr(result, "meta", None)
            assert result_meta is not None, (
                f"Prompt {name} did not include meta on result"
            )
            assert "machine_payload" in result_meta, (
                f"Prompt {name} missing machine_payload in meta"
            )


@pytest.mark.asyncio
async def test_list_prompts_descriptor_exposes_decorator_meta(test_app):
    """Ensure prompt descriptors returned by list_prompts expose the
    decorator-provided metadata as `.meta` so clients can discover schemas.
    """
    client = Client(test_app)
    async with client:
        prompts = await client.list_prompts()

    assert isinstance(prompts, list), "list_prompts did not return a list"
    assert len(prompts) > 0, "list_prompts returned an empty list"

    # Every prompt descriptor should at least have a `.meta` attribute (may be empty)
    for p in prompts:
        meta = getattr(p, "meta", None)
        assert meta is not None, (
            f"Prompt descriptor {getattr(p, 'name', '<no-name>')} missing .meta"
        )
