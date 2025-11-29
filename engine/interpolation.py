"""
Trajectory interpolation utilities for UAV deconfliction.

This module exposes:
    - interpolate_trajectory() → Linear interpolation of a drone path.

Trajectory interpolation is required to:
    • Normalize sampling rate between heterogeneous drone logs
    • Improve spatial conflict detection accuracy
    • Enable KD-Tree based nearest-neighbor spatial checks
"""

from __future__ import annotations

from typing import List, Tuple
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# LINEAR TRAJECTORY INTERPOLATION
# ---------------------------------------------------------------------------
def interpolate_trajectory(
    df_drone: pd.DataFrame,
    step_seconds: float = 0.5
) -> List[Tuple[pd.Timestamp, float, float, float]]:
    """
    Linearly interpolate a drone trajectory into evenly spaced time samples.

    Parameters
    ----------
    df_drone : pd.DataFrame
        Must contain a single drone's telemetry/waypoints with columns:
        ['Time', 'Latitude', 'Longitude', 'Altitude'].
        Must already be sorted by Time.

    step_seconds : float, optional
        Sampling interval in seconds.
        If <= 0, the function returns the raw input points unmodified.

    Returns
    -------
    list of tuples
        List of (timestamp, latitude, longitude, altitude) sampled points.

    Notes
    -----
    • This function performs simple linear interpolation between consecutive
      waypoints. It assumes straight-line motion between sample points.

    • Interpolation improves deconfliction accuracy and avoids missing
      conflicts that occur between logged timestamps.

    • If duplicated timestamps exist, zero-length intervals are skipped.
    """

    # ----------------------------------------------------------------------
    # 0. SHORT-CIRCUIT: If interpolation disabled → return raw tuples
    # ----------------------------------------------------------------------
    if step_seconds <= 0:
        return [
            (row["Time"], row["Latitude"], row["Longitude"], row["Altitude"])
            for _, row in df_drone.iterrows()
        ]

    rows: List[Tuple[pd.Timestamp, float, float, float]] = []

    # Extract arrays for efficiency
    times = df_drone["Time"].values
    lats = df_drone["Latitude"].values
    lons = df_drone["Longitude"].values
    alts = df_drone["Altitude"].values

    n_points = len(times)
    if n_points < 2:  # Only one waypoint → no interpolation needed
        return [
            (pd.Timestamp(times[0]), float(lats[0]), float(lons[0]), float(alts[0]))
        ]

    # ----------------------------------------------------------------------
    # 1. INTERPOLATE BETWEEN EACH PAIR OF WAYPOINTS
    # ----------------------------------------------------------------------
    for i in range(n_points - 1):

        t0 = pd.Timestamp(times[i])
        t1 = pd.Timestamp(times[i + 1])

        # Compute time gap in seconds
        dt = (t1 - t0).total_seconds()
        if dt <= 0:
            # Non-increasing timestamps → skip segment
            continue

        # Determine number of sampling steps
        n_steps = max(1, int(np.ceil(dt / step_seconds)))

        # ------------------------------------------------------------------
        # Generate interpolated samples between t0 → t1
        # ------------------------------------------------------------------
        for k in range(n_steps):
            frac = k / n_steps  # Fraction from start to end

            t = t0 + pd.Timedelta(seconds=frac * dt)
            lat = float(lats[i] + frac * (lats[i + 1] - lats[i]))
            lon = float(lons[i] + frac * (lons[i + 1] - lons[i]))
            alt = float(alts[i] + frac * (alts[i + 1] - alts[i]))

            rows.append((t, lat, lon, alt))

    # ----------------------------------------------------------------------
    # 2. Append final waypoint explicitly
    # ----------------------------------------------------------------------
    rows.append(
        (
            pd.Timestamp(times[-1]),
            float(lats[-1]),
            float(lons[-1]),
            float(alts[-1]),
        )
    )

    return rows
