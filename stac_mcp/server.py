from __future__ import annotations

import logging
from typing import Any

from fastmcp.server.server import FastMCP

from stac_mcp.prompts import register_prompts
from stac_mcp.tools import execution
from stac_mcp.tools.params import preprocess_parameters

app = FastMCP()

_LOGGER = logging.getLogger(__name__)

# Prompts are registered separately to keep the server module small and
# avoid import cycles. See `stac_mcp.prompts.register_prompts` for details.
register_prompts(app)


@app.tool
async def get_root() -> list[dict[str, Any]]:
    """Return the STAC root document for a catalog."""
    return await execution.execute_tool(
        "get_root", arguments={}, catalog_url=None, headers=None
    )


@app.tool
async def get_conformance() -> list[dict[str, Any]]:
    """Return server conformance classes."""
    return await execution.execute_tool(
        "get_conformance", arguments={}, catalog_url=None, headers=None
    )


@app.tool
async def search_collections(
    limit: int | None = 10, catalog_url: str | None = None
) -> list[dict[str, Any]]:
    """Return a page of STAC collections."""
    return await execution.execute_tool(
        "search_collections",
        arguments={"limit": limit},
        catalog_url=catalog_url,
        headers=None,
    )


@app.tool
async def get_collection(
    collection_id: str, catalog_url: str | None = None
) -> list[dict[str, Any]]:
    """Fetch a single STAC Collection by id."""
    return await execution.execute_tool(
        "get_collection",
        arguments={"collection_id": collection_id},
        catalog_url=catalog_url,
        headers=None,
    )


@app.tool
async def get_item(
    collection_id: str,
    item_id: str,
    output_format: str | None = "text",
    catalog_url: str | None = None,
) -> list[dict[str, Any]]:
    """Get a specific STAC Item by collection and item ID."""
    return await execution.execute_tool(
        "get_item",
        arguments={
            "collection_id": collection_id,
            "item_id": item_id,
            "output_format": output_format,
        },
        catalog_url=catalog_url,
        headers=None,
    )


@app.tool
async def search_items(
    collections: list[str],
    bbox: list[float] | None = None,
    datetime: str | None = None,
    limit: int | None = 10,
    query: dict[str, Any] | None = None,
    output_format: str | None = "text",
    catalog_url: str | None = None,
) -> list[dict[str, Any]]:
    """Search for STAC items."""
    arguments = preprocess_parameters(
        {
            "collections": collections,
            "bbox": bbox,
            "datetime": datetime,
            "limit": limit,
            "query": query,
            "output_format": output_format,
        }
    )
    return await execution.execute_tool(
        "search_items",
        arguments=arguments,
        catalog_url=catalog_url,
        headers=None,
    )


@app.tool
async def list_collection_keywords(
    catalog_url: str | None = None,
) -> list[dict[str, Any]]:
    """Return a lightweight mapping of collection IDs to their keywords or description summary. Use this to quickly identify which collections match a user's needs without fetching full metadata."""
    return await execution.execute_tool(
        "list_collection_keywords",
        arguments={},
        catalog_url=catalog_url,
        headers=None,
    )


@app.tool
async def get_queryables(
    collection_id: list[str],
    catalog_url: str | None = None,
) -> list[dict[str, Any]]:
    """Get the queryable properties for a specific STAC collection by its ID."""
    return await execution.execute_tool(
        "get_queryables",
        {"collection_id": collection_id},
        catalog_url=catalog_url,
        headers=None,
    )


@app.tool
async def get_aggregations(
    collections: list[str],
    bbox: list[float] | None = None,
    datetime: str | None = None,
    query: dict[str, Any] | None = None,
    catalog_url: str | None = None,
) -> list[dict[str, Any]]:
    """Get aggregations for STAC items."""
    return await execution.execute_tool(
        "get_aggregations",
        arguments={
            "collections": collections,
            "bbox": bbox,
            "datetime": datetime,
            "query": query,
        },
        catalog_url=catalog_url,
        headers=None,
    )


