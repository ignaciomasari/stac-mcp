import re

import pytest

from stac_mcp.utils.tabular import load_tabular_asset_as_xarray
from stac_mcp.utils.today import get_today_date


def test_tabular_stub_raises():
    """Ensure the removed tabular helper raises a clear NotImplementedError."""
    with pytest.raises(NotImplementedError) as excinfo:
        load_tabular_asset_as_xarray()
    assert "Parquet/Zarr tabular helpers have been removed" in str(excinfo.value)


def test_get_today_date_format():
    """get_today_date should return ISO YYYY-MM-DD string."""
    s = get_today_date()
    assert isinstance(s, str)
    assert re.match(r"^\d{4}-\d{2}-\d{2}$", s)
