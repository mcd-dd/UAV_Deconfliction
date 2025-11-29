# tests/test_altitude_conflicts.py
from engine.temporal import temporal_check_df
import pandas as pd

def test_altitude_conflict_detected(simple_df):
    """
    Make two drones vertically close while horizontal distance > threshold.
    Still should be detected in 3D.
    """
    df = simple_df.copy()

    # Align timestamps to guarantee a conflict
    df.loc[df["DroneID"] == 3, "Time"] = pd.Timestamp("2025-05-24 10:00:00")

    # Force spatial overlap
    df.loc[df["DroneID"] == 3, "Latitude"] = df[df["DroneID"] == 1].iloc[0]["Latitude"]
    df.loc[df["DroneID"] == 3, "Longitude"] = df[df["DroneID"] == 1].iloc[0]["Longitude"]

    # Force altitude conflict directly
    df.loc[df["DroneID"] == 3, "Altitude"] = df[df["DroneID"] == 1].iloc[0]["Altitude"] + 2



    violations = temporal_check_df(
        df,
        primary_id=1,
        time_window_sec=1.0,
        min_distance_meters=5  # very small threshold
    )
    assert len(violations) > 0
    assert violations[0][1]["DroneID"] == 3


def test_no_altitude_conflict(simple_df):
    """
    Far altitude → no 3D conflict.
    """
    df = simple_df.copy()
    df.loc[df["DroneID"] == 2, "Altitude"] = 500  # far above

    violations = temporal_check_df(
        df,
        primary_id=1,
        time_window_sec=2.0,
        min_distance_meters=20
    )
    assert len(violations) == 0
