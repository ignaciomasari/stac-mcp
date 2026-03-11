import pytest
from fastmcp.client import Client

from stac_mcp.server import app

NEW_PROMPTS = [
    "catalog_discovery_prompt",
    "collection_alias_resolution_prompt",
    "explain_tool_output_prompt",
]


@pytest.mark.asyncio
async def test_prompts_registered_and_return_machine_payload():
    client = Client(app)
    async with client:
        for name in NEW_PROMPTS:
            res = await client.get_prompt(name)
            assert hasattr(res, "messages")
            assert len(res.messages) > 0
            # In FastMCP 3.x, meta lives on the PromptResult, not individual messages
            result_meta = getattr(res, "meta", None)
            assert result_meta is not None, f"Prompt {name} should expose meta"
            assert "machine_payload" in result_meta, (
                f"Prompt {name} should include machine_payload"
            )
            payload = result_meta["machine_payload"]
            assert isinstance(payload, dict)
            assert "name" in payload
