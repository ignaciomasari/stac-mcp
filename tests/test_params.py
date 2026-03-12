"""Test parameter preprocessing for various input formats."""

import json

from stac_mcp.tools.params import preprocess_parameters


def test_bbox_as_string():
    """Test that bbox as JSON string is converted to list."""
    args = {"bbox": "[-123.27, 49.15, -123.0, 49.35]"}
    result = preprocess_parameters(args)
    assert result["bbox"] == [-123.27, 49.15, -123.0, 49.35]
    assert isinstance(result["bbox"], list)
    assert all(isinstance(x, float) for x in result["bbox"])


def test_bbox_as_list():
    """Test that bbox as list is preserved."""
    args = {"bbox": [-123.27, 49.15, -123.0, 49.35]}
    result = preprocess_parameters(args)
    assert result["bbox"] == [-123.27, 49.15, -123.0, 49.35]
    assert isinstance(result["bbox"], list)


def test_bbox_none():
    """Test that bbox as None is preserved."""
    args = {"bbox": None}
    result = preprocess_parameters(args)
    assert result["bbox"] is None


def test_limit_as_string():
    """Test that limit as string is converted to int."""
    args = {"limit": "5"}
    result = preprocess_parameters(args)
    assert result["limit"] == 5  # noqa: PLR2004
    assert isinstance(result["limit"], int)


def test_collections_as_string():
    """Test that collections as JSON string is converted to list."""
    args = {"collections": '["sentinel-2-l2a", "landsat-c2-l2"]'}
    result = preprocess_parameters(args)
    assert result["collections"] == ["sentinel-2-l2a", "landsat-c2-l2"]
    assert isinstance(result["collections"], list)


def test_collections_as_list():
    """Test that collections as list is preserved."""
    args = {"collections": ["sentinel-2-l2a", "landsat-c2-l2"]}
    result = preprocess_parameters(args)
    assert result["collections"] == ["sentinel-2-l2a", "landsat-c2-l2"]


def test_query_as_string():
    """Test that query as JSON string is converted to dict."""
    args = {"query": '{"eo:cloud_cover": {"lt": 10}}'}
    result = preprocess_parameters(args)
    assert isinstance(result["query"], dict)
    assert "eo:cloud_cover" in result["query"]


def test_query_as_dict():
    """Test that query as dict is preserved."""
    args = {"query": {"eo:cloud_cover": {"lt": 10}}}
    result = preprocess_parameters(args)
    assert isinstance(result["query"], dict)
    assert "eo:cloud_cover" in result["query"]


def test_empty_args():
    """Test that empty arguments are handled."""
    result = preprocess_parameters({})
    assert result == {}


def test_none_args():
    """Test that None arguments are handled."""
    result = preprocess_parameters(None)
    assert result is None


def test_invalid_json_string():
    """Test that invalid JSON strings are preserved as-is."""
    args = {"bbox": "not-valid-json"}
    result = preprocess_parameters(args)
    # Invalid JSON should be preserved as string (handler will deal with error)
    assert result["bbox"] == "not-valid-json"


def test_mixed_parameters():
    """Test preprocessing with mixed string and native types."""
    args = {
        "collections": '["sentinel-2-l2a"]',
        "bbox": [-123.27, 49.15, -123.0, 49.35],
        "datetime": "2025-01-01/2025-01-31",
        "limit": 10,
        "query": '{"eo:cloud_cover": {"lt": 10}}',
    }
    result = preprocess_parameters(args)
    assert isinstance(result["collections"], list)
    assert isinstance(result["bbox"], list)
    assert isinstance(result["query"], dict)
    assert result["datetime"] == "2025-01-01/2025-01-31"
    assert result["limit"] == 10  # noqa: PLR2004


def test_bbox_as_comma_separated_string():
    """Test that bbox as comma-separated string (not JSON) is converted to list."""
    args = {"bbox": "15.3626,47.0284,15.6321,47.1101"}
    result = preprocess_parameters(args)
    assert result["bbox"] == [15.3626, 47.0284, 15.6321, 47.1101]
    assert isinstance(result["bbox"], list)
    assert all(isinstance(x, float) for x in result["bbox"])


def test_bbox_as_comma_separated_string_with_spaces():
    """Test that bbox as comma-separated string with spaces is handled."""
    args = {"bbox": "15.3626, 47.0284, 15.6321, 47.1101"}
    result = preprocess_parameters(args)
    assert result["bbox"] == [15.3626, 47.0284, 15.6321, 47.1101]


def test_collections_as_plain_string():
    """Test that a single collection name string is wrapped in a list."""
    args = {"collections": "sentinel-2-l2a"}
    result = preprocess_parameters(args)
    assert result["collections"] == ["sentinel-2-l2a"]
    assert isinstance(result["collections"], list)


def test_collections_as_comma_separated_string():
    """Test that comma-separated collection names are split into a list."""
    args = {"collections": "sentinel-2-l2a, landsat-c2-l2"}
    result = preprocess_parameters(args)
    assert result["collections"] == ["sentinel-2-l2a", "landsat-c2-l2"]
    assert isinstance(result["collections"], list)
