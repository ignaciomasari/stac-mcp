"""Prompt registrations for the STAC MCP server.

This module exposes a single function `register_prompts(app)` which attaches
all prompt definitions to the provided FastMCP app. Keeping prompts in a
separate module avoids making the server module too large and prevents
import cycles.

Each prompt definition includes both the human-readable content and the
machine-readable payload schema and example. They aim to be epistemically
transparent about their purpose and usage - guiding users on geospatial data
tool interactions.
"""

from __future__ import annotations

import json
from typing import Any

from fastmcp.prompts.prompt import Message, PromptResult


def _make_result(human: str, payload: dict, description: str = "") -> PromptResult:
    """Build a PromptResult with machine_payload in meta."""
    return PromptResult(
        messages=[Message(human, role="user")],
        description=description,
        meta={"machine_payload": payload},
    )


def register_prompts(app: Any) -> None:
    """Register all prompt definitions on the provided FastMCP `app`."""
    _common_required = ["collections", "datetime", "bbox", "limit"]

    @app.prompt(
        name="stac_tool_overview_prompt",
        description="Overview of STAC tools available",
        meta={},
    )
    def _prompt_stac_tool_overview() -> PromptResult:
        human = (
            "Available STAC tools: get_root, get_conformance, search_collections, "
            "get_collection, get_queryables, search_items, get_item, "
            "get_aggregations, and list_collection_keywords."
        )
        payload = {
            "name": "stac_tool_overview",
            "description": "Overview of STAC tools available",
            "parameters": {},
            "example": {},
        }
        return _make_result(human, payload, "Overview of STAC tools available")

    @app.prompt(
        name="tool_get_root_prompt",
        description="Usage for get_root tool",
        meta={
            "schema": {"type": "object", "properties": {}, "required": []},
            "example": {},
        },
    )
    def _prompt_get_root() -> PromptResult:
        schema = {"type": "object", "properties": {}, "required": []}
        payload = {
            "name": "get_root",
            "description": "Return the STAC root document for a catalog.",
            "parameters": schema,
            "example": {},
        }
        human = (
            f"Tool: get_root\nDescription: {payload['description']}\n\n"
            "Parameters:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            "Example:\n"
            f"{json.dumps(payload['example'], indent=2)}"
        )
        return _make_result(human, payload, "Usage for get_root tool")

    @app.prompt(
        name="tool_get_conformance_prompt",
        description="Usage for get_conformance tool",
        meta={
            "schema": {"type": "object", "properties": {}, "required": []},
            "example": {},
        },
    )
    def _prompt_get_conformance() -> PromptResult:
        schema = {"type": "object", "properties": {}, "required": []}
        payload = {
            "name": "get_conformance",
            "description": "Return server conformance classes.",
            "parameters": schema,
            "example": {},
        }
        human = (
            f"Tool: get_conformance\nDescription: {payload['description']}\n\n"
            "Parameters:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            "Example:\n"
            f"{json.dumps(payload['example'], indent=2)}"
        )
        return _make_result(human, payload, "Usage for get_conformance tool")

    @app.prompt(
        name="tool_search_collections_prompt",
        description="Usage for search_collections tool",
        meta={
            "schema": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 10},
                    "catalog_url": {"type": "string"},
                },
                "required": [],
            },
            "example": {"limit": 5},
        },
    )
    def _prompt_search_collections() -> PromptResult:
        schema = {
            "type": "object",
            "properties": {
                "limit": {"type": "integer", "default": 10},
                "catalog_url": {"type": "string"},
            },
            "required": [],
        }
        payload = {
            "name": "search_collections",
            "description": "Return a page of STAC collections.",
            "parameters": schema,
            "example": {"limit": 5},
        }
        human = (
            f"Tool: search_collections\nDescription: {payload['description']}\n\n"
            "Parameters:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            "Example:\n"
            f"{json.dumps(payload['example'], indent=2)}"
        )
        return _make_result(human, payload, "Usage for search_collections tool")

    @app.prompt(
        name="tool_get_collection_prompt",
        description="Usage for get_collection tool",
        meta={
            "schema": {
                "type": "object",
                "properties": {
                    "collection_id": {"type": "string"},
                    "catalog_url": {"type": "string"},
                },
                "required": ["collection_id"],
            },
            "example": {"collection_id": "my-collection"},
        },
    )
    def _prompt_get_collection() -> PromptResult:
        schema = {
            "type": "object",
            "properties": {
                "collection_id": {"type": "string"},
                "catalog_url": {"type": "string"},
            },
            "required": ["collection_id"],
        }
        payload = {
            "name": "get_collection",
            "description": "Fetch a single STAC Collection by id.",
            "parameters": schema,
            "example": {"collection_id": "my-collection"},
        }
        human = (
            f"Tool: get_collection\nDescription: {payload['description']}\n\n"
            "Parameters:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            "Example:\n"
            f"{json.dumps(payload['example'], indent=2)}"
        )
        return _make_result(human, payload, "Usage for get_collection tool")

    @app.prompt(
        name="tool_get_item_prompt",
        description="Usage for get_item tool",
        meta={
            "schema": {
                "type": "object",
                "properties": {
                    "collection_id": {"type": "string"},
                    "item_id": {"type": "string"},
                    "output_format": {
                        "type": "string",
                        "enum": ["text", "json"],
                        "default": "text",
                    },
                    "catalog_url": {"type": "string"},
                },
                "required": ["collection_id", "item_id"],
            },
            "example": {
                "collection_id": "c1",
                "item_id": "i1",
                "output_format": "json",
            },
        },
    )
    def _prompt_get_item() -> PromptResult:
        schema = {
            "type": "object",
            "properties": {
                "collection_id": {"type": "string"},
                "item_id": {"type": "string"},
                "output_format": {
                    "type": "string",
                    "enum": ["text", "json"],
                    "default": "text",
                },
                "catalog_url": {"type": "string"},
            },
            "required": ["collection_id", "item_id"],
        }
        payload = {
            "name": "get_item",
            "description": "Retrieve a single STAC Item.",
            "parameters": schema,
            "example": {
                "collection_id": "c1",
                "item_id": "i1",
                "output_format": "json",
            },
        }
        human = (
            f"Tool: get_item\nDescription: {payload['description']}\n\n"
            "Parameters:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            "Example:\n"
            f"{json.dumps(payload['example'], indent=2)}"
        )
        return _make_result(human, payload, "Usage for get_item tool")

    @app.prompt(
        name="tool_search_items_prompt",
        description="Usage for search_items tool",
        meta={
            "schema": {
                "type": "object",
                "properties": {
                    "collections": {"type": "array", "items": {"type": "string"}},
                    "bbox": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "datetime": {"type": "string"},
                    "limit": {"type": "integer", "default": 10},
                    "query": {"type": "object"},
                    "output_format": {
                        "type": "string",
                        "enum": ["text", "json"],
                        "default": "text",
                    },
                },
                "required": _common_required,
            },
            "example": {"collections": ["c1"], "limit": 3},
        },
    )
    def _prompt_search_items() -> PromptResult:
        schema = {
            "type": "object",
            "properties": {
                "collections": {"type": "array", "items": {"type": "string"}},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "datetime": {"type": "string"},
                "limit": {"type": "integer", "default": 10},
                "query": {"type": "object"},
                "output_format": {
                    "type": "string",
                    "enum": ["text", "json"],
                    "default": "text",
                },
            },
            "required": _common_required,
        }
        payload = {
            "name": "search_items",
            "description": "Search for STAC Items.",
            "parameters": schema,
            "example": {"collections": ["c1"], "limit": 3},
        }
        human = (
            f"Tool: search_items\nDescription: {payload['description']}\n\n"
            "Parameters:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            "Example:\n"
            f"{json.dumps(payload['example'], indent=2)}\n\n"
            "Notes:\n"
            "If get_collections has not been run yet for the target catalog, "
            "run it first to populate the collection list.\n"
            "On responses with zero items, validate that the collection IDs "
            "are correct.\n"
            "If using 'bbox', ensure coordinates are in [minLon, minLat, maxLon, "
            "maxLat] order.\n"
            "Datetime should be in ISO 8601 format, e.g., '2020-01-01/2020-12-31'.\n"
            "Limit should be a positive integer.\n"
            "Unlike `pystac-client`, this `limit` is a hard cutoff on the number "
            "of items returned post-search, not a page size.\n"
            "If a user specifies 'latest' for datetime, interpret it as the "
            "most recent available data for the specified collections and "
            "use a limit=1.\n"
            "To prevent excessive data retrieval, enforce a maximum limit of 10. "
            "Requests exceeding this limit should be adjusted down to 10 and batched.\n"
            "If 'query' is provided, ensure it conforms to the STAC API "
            "filter specification."
        )
        return _make_result(human, payload, "Usage for search_items tool")

    @app.prompt(
        name="tool_list_collection_keywords_prompt",
        description="Usage for list_collection_keywords tool",
        meta={
            "schema": {
                "type": "object",
                "properties": {
                    "catalog_url": {"type": "string"},
                },
                "required": [],
            },
            "example": {},
        },
    )
    def _prompt_list_collection_keywords() -> PromptResult:
        schema = {
            "type": "object",
            "properties": {
                "catalog_url": {"type": "string"},
            },
            "required": [],
        }
        payload = {
            "name": "list_collection_keywords",
            "description": (
                "Return a lightweight mapping of collection IDs to their "
                "keywords or description summary."
            ),
            "parameters": schema,
            "example": {},
        }
        human = (
            f"Tool: list_collection_keywords\n"
            f"Description: {payload['description']}\n\n"
            "Parameters:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            "Use this tool first to identify which collections are relevant "
            "to the user's query without fetching full metadata.\n\n"
            "Example:\n"
            f"{json.dumps(payload['example'], indent=2)}"
        )
        return _make_result(human, payload, "Usage for list_collection_keywords tool")

    @app.prompt(
        name="tool_get_queryables_prompt",
        description="Usage for get_queryables tool",
        meta={
            "schema": {
                "type": "object",
                "properties": {
                    "collection_id": {"type": "string"},
                    "catalog_url": {"type": "string"},
                },
                "required": [],
            },
            "example": {"collection_id": "my-collection"},
        },
    )
    def _prompt_get_queryables() -> PromptResult:
        schema = {
            "type": "object",
            "properties": {
                "collection_id": {"type": "string"},
                "catalog_url": {"type": "string"},
            },
            "required": [],
        }
        payload = {
            "name": "get_queryables",
            "description": "Fetch STAC API (or collection) queryables.",
            "parameters": schema,
            "example": {"collection_id": "my-collection"},
        }
        human = (
            f"Tool: get_queryables\nDescription: {payload['description']}\n\n"
            "Parameters:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            "Example:\n"
            f"{json.dumps(payload['example'], indent=2)}"
        )
        return _make_result(human, payload, "Usage for get_queryables tool")

    @app.prompt(
        name="tool_get_aggregations_prompt",
        description="Usage for get_aggregations tool",
        meta={
            "schema": {
                "type": "object",
                "properties": {
                    "collections": {"type": "array", "items": {"type": "string"}},
                    "bbox": {
                        "type": "array",
                        "items": {"type": "number"},
                        "minItems": 4,
                        "maxItems": 4,
                    },
                    "datetime": {"type": "string"},
                    "query": {"type": "object"},
                    "catalog_url": {"type": "string"},
                },
                "required": _common_required,
            },
            "example": {"collections": ["c1"], "datetime": "2020-01-01/2020-12-31"},
        },
    )
    def _prompt_get_aggregations() -> PromptResult:
        schema = {
            "type": "object",
            "properties": {
                "collections": {"type": "array", "items": {"type": "string"}},
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4,
                    "maxItems": 4,
                },
                "datetime": {"type": "string"},
                "query": {"type": "object"},
                "catalog_url": {"type": "string"},
            },
            "required": _common_required,
        }
        payload = {
            "name": "get_aggregations",
            "description": "Return aggregations for STAC Items in a collection.",
            "parameters": schema,
            "example": {"collections": ["c1"], "datetime": "2020-01-01/2020-12-31"},
        }
        human = (
            f"Tool: get_aggregations\nDescription: {payload['description']}\n\n"
            "Parameters:\n"
            f"{json.dumps(schema, indent=2)}\n\n"
            "Example:\n"
            f"{json.dumps(payload['example'], indent=2)}"
        )
        return _make_result(human, payload, "Usage for get_aggregations tool")

    @app.prompt(
        name="tool_ordering_info_prompt",
        description="Information on tool ordering and usage",
        meta={},
    )
    def _prompt_tool_ordering_info() -> PromptResult:
        human = (
            "Preferred order: list_collection_keywords (to identify relevant "
            "collections) -> get_root -> get_conformance -> search_collections -> "
            "get_collection -> get_queryables -> search_items -> get_item. "
            "Use caching and sampling (limit) to control response size."
        )
        payload = {
            "name": "tool_ordering_info",
            "description": "Preferred order and usage guidance for STAC tools",
            "parameters": {},
            "example": {},
        }
        return _make_result(human, payload, "Tool ordering information")

    @app.prompt(
        name="catalog_discovery_prompt",
        description="Steps to discover what a STAC catalog supports",
        meta={},
    )
    def _prompt_catalog_discovery() -> PromptResult:
        human = (
            "Discovery steps:\n"
            "1) Call get_root to locate the catalog root and entrypoints.\n"
            "2) Call get_conformance to list supported STAC extensions.\n"
            "3) Run search_collections (limit=50) to inspect available "
            "collection IDs and titles.\n"
            "4) Sample get_collection for candidate collections to validate "
            "assets and links.\n\n"
            "Parameters:\n"
            "- None\n\n"
            "Example:\n"
            '{"catalog_url": "https://planetarycomputer.microsoft.com/api/stac/v1"}\n\n'
            "Notes:\n"
            "Use these steps before searching items to avoid mismatched "
            "collection IDs."
        )
        payload = {
            "name": "catalog_discovery",
            "description": "Checklist for discovering catalog capabilities",
            "parameters": {},
            "example": {},
        }
        return _make_result(human, payload, "Catalog discovery steps")

    @app.prompt(
        name="collection_alias_resolution_prompt",
        description="How to resolve collection id aliases across catalogs",
        meta={},
    )
    def _prompt_collection_alias_resolution() -> PromptResult:
        human = (
            "Alias resolution strategy:\n"
            "1) When a collection ID lookup returns no result, normalize case "
            "and punctuation.\n"
            "2) Try provider-specific aliases (for example: 'sentinel-2-l2a' "
            "vs 'sentinel-2-c1-l2a').\n"
            "3) Use list_collection_keywords to scan available collections by "
            "keyword.\n"
            "4) For each candidate alias call get_collection to verify presence "
            "and canonical metadata.\n\n"
            "Parameters:\n"
            "- collection_id: string (optional)\n\n"
            "Example:\n"
            '{"collection_id": "sentinel-2-c1-l2a"}\n'
        )
        payload = {
            "name": "collection_alias_resolution",
            "description": "Steps to resolve collection id aliases across providers",
            "parameters": {},
            "example": {},
        }
        return _make_result(human, payload, "Collection alias resolution")

    @app.prompt(
        name="explain_tool_output_prompt",
        description="Summarize and explain tool outputs for humans",
        meta={
            "schema": {
                "type": "object",
                "properties": {
                    "tool": {"type": "string"},
                    "payload": {"type": "object"},
                },
                "required": ["tool", "payload"],
            },
            "example": {"tool": "get_collection", "payload": {}},
        },
    )
    def _prompt_explain_tool_output() -> PromptResult:
        schema = {
            "type": "object",
            "properties": {"tool": {"type": "string"}, "payload": {"type": "object"}},
            "required": ["tool", "payload"],
        }
        payload = {
            "name": "explain_tool_output",
            "description": "Summarize and explain tool outputs",
            "parameters": schema,
            "example": {"tool": "get_collection", "payload": {}},
        }
        human = (
            "Explain tool output:\n"
            "- Give a 2-4 sentence human summary of the tool output.\n"
            "- Highlight 3 most important fields and why they matter.\n"
            "- Provide 1-2 concrete next steps (e.g., call ordering or "
            "validation checks).\n\n"
            "Parameters:\n"
            "- tool: string\n"
            "- payload: object (the tool response)\n\n"
            "Example:\n"
            '{"tool": "get_collection", "payload": {}}\n'
        )
        return _make_result(human, payload, "Explain tool output")
