# tests/test_temporal_conflicts.py
import pandas as pd
from datetime import datetime
from engine.temporal import temporal_check_df


def test_temporal_conflict_detected(simple_df):
    """Primary and Drone 2 share timestamp → conflict expected."""
    violations = temporal_check_df(
        simple_df,
        primary_id=1,
        time_window_sec=1.0,
        min_distance_meters=20
    )
    assert len(violations) > 0
    assert violations[0][1]["DroneID"] == 2


def test_no_temporal_conflict_outside_window(simple_df):
    """Drone with far-apart timestamps should not conflict."""
    df = simple_df.copy()
    df.loc[df["DroneID"] == 2, "Time"] = datetime(2025, 5, 24, 10, 5, 0)

    violations = temporal_check_df(
        df,
        primary_id=1,
        time_window_sec=2.0,
        min_distance_meters=20
    )
    assert len(violations) == 0
