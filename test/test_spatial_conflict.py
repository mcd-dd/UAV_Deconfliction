# tests/test_spatial_conflicts.py
from engine.spatial import spatial_check_with_index


def test_spatial_conflict_detected(simple_df):
    """Drone 2 is within ~15 meters → conflict expected."""
    primary_wp = [
        (
            simple_df.iloc[0]["Time"],
            simple_df.iloc[0]["Latitude"],
            simple_df.iloc[0]["Longitude"],
            simple_df.iloc[0]["Altitude"],
        )
    ]

    other_wps = [
        row._asdict() if hasattr(row, "_asdict") else row.to_dict()
        for _, row in simple_df[simple_df["DroneID"] == 2].iterrows()
    ]

    violations = spatial_check_with_index(primary_wp, other_wps, min_distance_meters=20)
    assert len(violations) > 0
    assert violations[0][1]["DroneID"] == 2


def test_no_spatial_conflict_when_far(simple_df):
    """Drone 3 is far away → no conflict."""
    primary_wp = [
        (
            simple_df.iloc[0]["Time"],
            simple_df.iloc[0]["Latitude"],
            simple_df.iloc[0]["Longitude"],
            simple_df.iloc[0]["Altitude"],
        )
    ]
    other_wps = [
        row.to_dict()
        for _, row in simple_df[simple_df["DroneID"] == 3].iterrows()
    ]

    violations = spatial_check_with_index(primary_wp, other_wps, min_distance_meters=30)
    assert len(violations) == 0
