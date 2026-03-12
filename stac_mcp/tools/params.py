"""Parameter preprocessing utilities for handling various input formats."""

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


def preprocess_parameters(arguments: dict[str, Any]) -> dict[str, Any]:
    """Preprocess tool parameters to handle various input formats.

    This function normalizes parameters that may come in as strings but should be
    other types (arrays, objects, etc.). This is particularly useful when MCP clients
    serialize parameters as strings.

    Args:
        arguments: Raw arguments dictionary from MCP client

    Returns:
        Preprocessed arguments with proper types
    """
    if not arguments:
        return arguments

    processed = arguments.copy()

    # Handle bbox parameter - should be a list of 4 floats
    if "bbox" in processed and processed["bbox"] is not None:
        bbox = processed["bbox"]
        if isinstance(bbox, str):
            parsed_bbox = None
            try:
                parsed = json.loads(bbox)
                if isinstance(parsed, list) and len(parsed) == 4:  # noqa: PLR2004
                    parsed_bbox = [float(x) for x in parsed]
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
            if parsed_bbox is None:
                try:
                    parts = [p.strip() for p in bbox.split(",")]
                    if len(parts) == 4:  # noqa: PLR2004
                        parsed_bbox = [float(x) for x in parts]
                except (ValueError, TypeError):
                    logger.warning("Failed to parse bbox string: %s", bbox)
            if parsed_bbox is not None:
                processed["bbox"] = parsed_bbox
                logger.debug("Converted bbox from string to list: %s", parsed_bbox)

    # Handle collections parameter - should be a list of strings
    if "collections" in processed and processed["collections"] is not None:
        collections = processed["collections"]
        if isinstance(collections, str):
            parsed_collections = None
            try:
                parsed = json.loads(collections)
                if isinstance(parsed, list):
                    parsed_collections = parsed
            except (json.JSONDecodeError, ValueError, TypeError):
                pass
            if parsed_collections is None:
                parsed_collections = [c.strip() for c in collections.split(",") if c.strip()]
            processed["collections"] = parsed_collections
            logger.debug(
                "Converted collections from string to list: %s",
                parsed_collections,
            )

    # Handle query parameter - should be a dict/object
    if "query" in processed and processed["query"] is not None:
        query = processed["query"]
        if isinstance(query, str):
            try:
                parsed = json.loads(query)
                if isinstance(parsed, dict):
                    processed["query"] = parsed
                    logger.debug("Converted query from string to dict")
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                logger.warning("Failed to parse query string: %s, error: %s", query, e)

    if "limit" in processed and processed["limit"] is not None:
        limit = processed["limit"]
        if isinstance(limit, str):
            try:
                processed["limit"] = int(limit)
                logger.debug(
                    "Converted limit from string to int: %d", processed["limit"]
                )
            except ValueError as e:
                logger.warning(
                    "Failed to convert limit string to int: %s, error: %s", limit, e
                )

    return processed
