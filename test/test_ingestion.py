# tests/test_ingestion.py
import pandas as pd
from ingestion.loader import load_waypoints_from_excel
import pytest


def test_ingestion_loads_excel(tmp_path):
    """Ensure Excel ingestion returns a clean DataFrame."""
    test_file = tmp_path / "test.xlsx"

    df_in = pd.DataFrame({
        "DroneID": [1, 2],
        "Time": ["2025-01-01 10:00:00", "2025-01-01 10:00:30"],
        "Latitude": [30.2, 30.21],
        "Longitude": [-119.9, -119.91],
        "Altitude": [100, 120]
    })
    df_in.to_excel(test_file, index=False)

    df_out = load_waypoints_from_excel(test_file)

    assert isinstance(df_out, pd.DataFrame)
    assert list(df_out.columns) == ["DroneID", "Time", "Latitude", "Longitude", "Altitude"]
    assert df_out["DroneID"].dtype == int
    assert pd.api.types.is_datetime64_any_dtype(df_out["Time"])
