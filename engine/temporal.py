"""
Temporal deconfliction module for UAV trajectory safety analysis.

This module performs:
    • Time-window filtering of potential conflicts.
    • Accurate 3D distance computation between UAVs at similar timestamps.

A temporal conflict occurs when two UAVs:
    1. Are within a user-defined time window, and
    2. Are spatially closer than the minimum allowed separation.
"""

from __future__ import annotations

from typing import List, Tuple, Dict
import math
import pandas as pd

from utils.geo import safe_geodesic_meters


# ---------------------------------------------------------------------------
# TEMPORAL CONFLICT CHECK
# ---------------------------------------------------------------------------
def temporal_check_df(
    df: pd.DataFrame,
    primary_id: int,
    time_window_sec: float,
    min_distance_meters: float
) -> List[Tuple[Tuple, Dict, float]]:
    """
    Perform temporal conflict detection using a sliding time window.

    Parameters
    ----------
    df : pandas.DataFrame
        Must contain the following columns:
        ['DroneID', 'Time', 'Latitude', 'Longitude', 'Altitude']

    primary_id : int
        ID of the primary UAV whose mission is being checked.

    time_window_sec : float
        Seconds before/after the primary timestamp to consider for conflicts.

    min_distance_meters : float
        Minimum allowed 3D separation distance.

    Returns
    -------
    list of tuples
        Each entry is:
            (primary_waypoint_tuple, other_waypoint_dict, distance_meters)

        Where:
            primary_waypoint_tuple = (timestamp, lat, lon, alt)
            other_waypoint_dict    = row.to_dict()
            distance_meters        = 3D separation

    Notes
    -----
    • A temporal conflict is only checked when timestamps fall within:
        [primary_time − window, primary_time + window]

    • Full 3D distance is computed as:
        sqrt( horizontal_geodesic^2 + altitude_difference^2 )
    """

    # Extract primary and other drone paths
    primary_path = df[df["DroneID"] == primary_id]
    other_paths = df[df["DroneID"] != primary_id]

    violations = []

    # If no data available → no conflicts
    if primary_path.empty or other_paths.empty:
        return violations

    time_window = pd.Timedelta(seconds=time_window_sec)

    # ----------------------------------------------------------------------
    # Loop through all primary UAV timestamps
    # ----------------------------------------------------------------------
    for _, prow in primary_path.iterrows():

        p_time = prow["Time"]
        p_lat = prow["Latitude"]
        p_lon = prow["Longitude"]
        p_alt = prow["Altitude"]

        primary_wp = (p_time, p_lat, p_lon, p_alt)

        # --------------------------------------------------------------
        # Filter other drones within the time window
        # --------------------------------------------------------------
        window_df = other_paths[
            (other_paths["Time"] >= p_time - time_window)
            & (other_paths["Time"] <= p_time + time_window)
        ]

        if window_df.empty:
            continue

        # --------------------------------------------------------------
        # Compute precise 3D distance for each candidate
        # --------------------------------------------------------------
        for _, orow in window_df.iterrows():

            horiz_dist = safe_geodesic_meters(
                p_lat, p_lon,
                orow["Latitude"], orow["Longitude"]
            )

            alt_diff = abs(p_alt - orow["Altitude"])
            dist_3d = math.sqrt(horiz_dist**2 + alt_diff**2)

            if dist_3d < min_distance_meters:
                violations.append((primary_wp, orow.to_dict(), dist_3d))

    return violations
