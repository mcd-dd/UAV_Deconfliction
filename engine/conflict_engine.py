"""
Conflict detection engine for UAV strategic deconfliction.

This module exposes:
1. `query_mission_status()` → High-level interface used by REST APIs / services.
2. `check_primary_mission_conflicts()` → Core engine performing:
       - Trajectory interpolation
       - Spatial conflict checks
       - Temporal conflict checks

The engine follows a modular design:
- engine.interpolation → Trajectory resampling
- engine.spatial        → Spatial minimum-distance checks
- engine.temporal       → Temporal overlap checks
"""

from __future__ import annotations

from typing import Dict, List, Tuple
import pandas as pd

from engine.interpolation import interpolate_trajectory
from engine.spatial import spatial_check_with_index
from engine.temporal import temporal_check_df


# ---------------------------------------------------------------------------
# PUBLIC QUERY INTERFACE
# ---------------------------------------------------------------------------
def query_mission_status(
    df: pd.DataFrame,
    primary_id: int,
    min_distance_meters: float = 10.0,
    time_window_sec: float = 1.0,
    interp_step_sec: float = 0.5
) -> Dict[str, object]:
    """
    High-level mission deconfliction query for external systems.

    This function is intended for:
    - REST API endpoints
    - Microservices
    - Real-time monitoring systems
    - CLI tools

    Parameters
    ----------
    df : pd.DataFrame
        Drone telemetry/waypoint dataset with columns:
        ['DroneID', 'Time', 'Latitude', 'Longitude', 'Altitude']

    primary_id : int
        UAV ID whose mission is to be checked.

    min_distance_meters : float, optional
        Minimum required separation distance between drones.

    time_window_sec : float, optional
        Temporal separation window (± seconds) for conflict detection.

    interp_step_sec : float, optional
        Resampling interval in seconds. Higher values → faster but less precise.

    Returns
    -------
    dict
        {
           "status": "clear" | "conflict detected",
           "spatial_conflicts": [...],
           "temporal_conflicts": [...]
        }
    """

    spatial_conflicts, temporal_conflicts = check_primary_mission_conflicts(
        df=df,
        primary_id=primary_id,
        min_distance_meters=min_distance_meters,
        time_window_sec=time_window_sec,
        interp_step_sec=interp_step_sec
    )

    status = (
        "clear"
        if not spatial_conflicts and not temporal_conflicts
        else "conflict detected"
    )

    return {
        "status": status,
        "spatial_conflicts": spatial_conflicts,
        "temporal_conflicts": temporal_conflicts,
    }


# ---------------------------------------------------------------------------
# CORE CONFLICT ENGINE
# ---------------------------------------------------------------------------
def check_primary_mission_conflicts(
    df: pd.DataFrame,
    primary_id: int,
    min_distance_meters: float = 10.0,
    time_window_sec: float = 1.0,
    interp_step_sec: float = 0.5
) -> Tuple[List, List]:
    """
    Perform full spatial + temporal conflict detection for a primary drone.

    Workflow
    --------
    1. Interpolate trajectories for primary + other drones
    2. Run spatial minimum-distance checks (KD-Tree optimized)
    3. Run temporal overlap checks

    Parameters
    ----------
    df : pd.DataFrame
        Waypoint dataset with columns:
        ['DroneID', 'Time', 'Latitude', 'Longitude', 'Altitude']

    primary_id : int
        Drone ID to test conflicts against.

    min_distance_meters : float
        Required horizontal/3D minimum separation distance.

    time_window_sec : float
        Allowed timestamp difference for temporal deconfliction.

    interp_step_sec : float
        Resampling interval for consistent time resolution.

    Returns
    -------
    (spatial_conflicts, temporal_conflicts)
        Lists containing tuples of (primary_wp, other_wp, distance).
    """

    # ----------------------------------------------------------------------
    # 1. EXTRACT + RESAMPLE OTHER DRONE TRAJECTORIES
    # ----------------------------------------------------------------------
    other_waypoints = []
    for drone_id, group in df.groupby("DroneID"):

        # Skip the primary drone at this stage
        if drone_id == primary_id:
            continue

        group_sorted = group.sort_values("Time")

        if interp_step_sec > 0:
            # Resample trajectory into evenly spaced samples
            samples = interpolate_trajectory(
                group_sorted, step_seconds=interp_step_sec
            )
            for t, lat, lon, alt in samples:
                other_waypoints.append(
                    {
                        "DroneID": drone_id,
                        "Time": t,
                        "Latitude": lat,
                        "Longitude": lon,
                        "Altitude": alt,
                    }
                )
        else:
            # Use raw points without interpolation
            for _, row in group_sorted.iterrows():
                other_waypoints.append(
                    {
                        "DroneID": drone_id,
                        "Time": row["Time"],
                        "Latitude": row["Latitude"],
                        "Longitude": row["Longitude"],
                        "Altitude": row["Altitude"],
                    }
                )

    # ----------------------------------------------------------------------
    # 2. RESAMPLE PRIMARY DRONE TRAJECTORY
    # ----------------------------------------------------------------------
    primary_df = df[df["DroneID"] == primary_id].sort_values("Time")

    if primary_df.empty:
        # No path → no conflicts
        return [], []

    if interp_step_sec > 0:
        primary_waypoints = interpolate_trajectory(
            primary_df, step_seconds=interp_step_sec
        )
    else:
        primary_waypoints = [
            (row["Time"], row["Latitude"], row["Longitude"], row["Altitude"])
            for _, row in primary_df.iterrows()
        ]

    # ----------------------------------------------------------------------
    # 3. SPATIAL CONFLICT CHECK
    # ----------------------------------------------------------------------
    spatial_conflicts = spatial_check_with_index(
        primary_waypoints,
        other_waypoints,
        min_distance_meters=min_distance_meters,
    )

    # ----------------------------------------------------------------------
    # 4. TEMPORAL CONFLICT CHECK
    # ----------------------------------------------------------------------
    temporal_conflicts = temporal_check_df(
        df=df,
        primary_id=primary_id,
        time_window_sec=time_window_sec,
        min_distance_meters=min_distance_meters,
    )

    # ----------------------------------------------------------------------
    # 5. RETURN BOTH RESULTS
    # ----------------------------------------------------------------------
    return spatial_conflicts, temporal_conflicts
