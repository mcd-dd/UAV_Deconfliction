# tests/conftest.py
import pytest
import pandas as pd
from datetime import datetime, timedelta

@pytest.fixture
def simple_df():
    """A tiny dataset for basic engine tests."""
    rows = [
        # Primary
        (1, datetime(2025, 5, 24, 10, 0, 0), 30.25, -119.95, 100),
        (1, datetime(2025, 5, 24, 10, 0, 30), 30.251, -119.951, 120),

        # Drone 2 (near)
        (2, datetime(2025, 5, 24, 10, 0, 0), 30.2501, -119.9501, 100),
        (2, datetime(2025, 5, 24, 10, 0, 30), 30.2511, -119.9511, 120),

        # Drone 3 (far)
        (3, datetime(2025, 5, 24, 10, 0, 0), 30.4, -120.2, 200),
    ]
    df = pd.DataFrame(rows, columns=["DroneID", "Time", "Latitude", "Longitude", "Altitude"])
    return df
