"""Handler for the list_collection_keywords tool."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent

from stac_mcp.tools.client import STACClient


def handle_list_collection_keywords(
    client: STACClient,
    arguments: dict[str, Any],
) -> list[TextContent] | dict[str, Any]:
    """Return a lightweight dict mapping collection IDs to keywords."""
    keywords = client.list_collection_keywords()

    if arguments.get("output_format") == "json":
        return {
            "type": "collection_keywords",
            "count": len(keywords),
            "collections": keywords,
        }

    result_text = f"Collection keywords ({len(keywords)} collections):\n\n"
    for collection_id, kw in keywords.items():
        if isinstance(kw, list):
            result_text += f"- {collection_id}: {', '.join(kw)}\n"
        else:
            result_text += f"- {collection_id}: {kw}\n"

    return [TextContent(type="text", text=result_text)]
