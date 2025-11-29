"""
Spatial deconfliction utilities for UAV trajectory analysis.

This module provides:
    • build_spatial_index() - Build KD-Tree for fast nearest-neighbor lookup.
    • spatial_check_with_index() - Detect spatial violations using the KD-Tree.

We approximate lat/lon → meters using an equirectangular projection for
KD-tree candidate pruning, but final distance computation uses accurate
geodesic (or haversine fallback).
"""

from __future__ import annotations

from typing import List, Dict, Tuple, Optional
import math
import numpy as np
from scipy.spatial import cKDTree
from datetime import timedelta
from utils.geo import safe_geodesic_meters


# ---------------------------------------------------------------------------
# BUILD SPATIAL KD-TREE FOR FAST NEAREST-NEIGHBOR SEARCH
# ---------------------------------------------------------------------------
def build_spatial_index(
    other_waypoints: List[Dict[str, float]]
) -> Tuple[Optional[cKDTree], Optional[np.ndarray], float]:
    """
    Construct a KD-Tree for horizontal (lat/lon) positions.

    Parameters
    ----------
    other_waypoints : list of dict
        Each dict must contain:
        {
            'Latitude': float,
            'Longitude': float,
            'Time': pd.Timestamp,
            'DroneID': int,
            'Altitude': float
        }

    Returns
    -------
    tree : cKDTree or None
        KD-Tree built from horizontal positions. None if no waypoints exist.

    points_np : np.ndarray or None
        N×2 array of projected (x,y) meter coordinates.

    lat_ref : float
        Mean latitude reference used for projection scaling.

    Notes
    -----
    • Uses an equirectangular projection:
        x = lon * cos(lat_ref) * meters_per_degree
        y = lat * meters_per_degree

    • meters_per_degree ≈ 111,320 m (approx Earth meridian distance).
    """

    if not other_waypoints:
        return None, None, 0.0

    # Mean latitude defines projection scale
    lat_ref = float(np.mean([wp["Latitude"] for wp in other_waypoints]))

    meters_per_degree = 111_320.0
    cos_ref = math.cos(math.radians(lat_ref))

    points: List[Tuple[float, float]] = []

    # Project lat/lon → (x,y) in meters
    for wp in other_waypoints:
        x = wp["Longitude"] * meters_per_degree * cos_ref
        y = wp["Latitude"] * meters_per_degree
        points.append((x, y))

    points_np = np.array(points, dtype=float)

    if points_np.size == 0:
        return None, points_np, lat_ref

    tree = cKDTree(points_np)
    return tree, points_np, lat_ref


# ---------------------------------------------------------------------------
# SPATIAL CONFLICT CHECK USING KD-TREE PRUNING
# ---------------------------------------------------------------------------
def spatial_check_with_index(
    primary_waypoints: List[Tuple],
    other_waypoints: List[Dict[str, float]],
    min_distance_meters: float
) -> List[Tuple[Tuple, Dict[str, float], float]]:
    """
    Detect spatial conflicts between the primary UAV and all other UAVs.

    Parameters
    ----------
    primary_waypoints : list of tuples
        Each tuple is:
            (time, lat, lon, alt)

    other_waypoints : list of dict
        Each dict contains:
            ['DroneID','Time','Latitude','Longitude','Altitude']

    min_distance_meters : float
        Safety threshold. A violation occurs when 3D distance < threshold.

    Returns
    -------
    list of tuples
        Each element:
            (primary_waypoint_tuple, other_waypoint_dict, distance_meters)

    Notes
    -----
    • KD-Tree prunes the number of distance checks drastically.
    • Horizontal candidate hits are verified using accurate geodesic distance
      and altitude difference.
    """

    tree, points_np, lat_ref = build_spatial_index(other_waypoints)

    # No other drones → no conflicts
    if tree is None:
        return []

    meters_per_degree = 111_320.0
    cos_ref = math.cos(math.radians(lat_ref))

    violations: List[Tuple[Tuple, Dict[str, float], float]] = []

    # ----------------------------------------------------------------------
    # 1. For each primary waypoint → convert to (x,y) meters → query KD-Tree
    # ----------------------------------------------------------------------
    for p_wp in primary_waypoints:

        (p_time, plat, plon, palt) = p_wp

        px = plon * meters_per_degree * cos_ref
        py = plat * meters_per_degree

        # KD-Tree: search radius in meters
        candidate_idxs = tree.query_ball_point([px, py], r=min_distance_meters)

        # ------------------------------------------------------------------
        # 2. For each candidate → compute precise geodesic 3D distance
        # ------------------------------------------------------------------
        for idx in candidate_idxs:

            o_wp = other_waypoints[idx]

            # # ---------------------------------------------------------
            # # NEW: Apply TIME FILTER (prevents false spatial conflicts)
            # # ---------------------------------------------------------
            # p_time = p_wp[0]           # Timestamp of primary waypoint
            # o_time = o_wp["Time"]      # Timestamp of other waypoint

            # # If time difference is too large → ignore (not a real conflict)
            # time_diff = abs((p_time - o_time).total_seconds())

            # # Adjust this tolerance as needed
            TIME_TOLERANCE_SEC = 0.1     # Small window is realistic for UAV deconfliction

            # if time_diff > TIME_TOLERANCE_SEC:
            #     continue  # Skip spatial checks when time windows do not overlap

            o_time = o_wp["Time"]

            # --------------------------------------------------
            # TIME FILTER – ignore spatial matches not near in time
            # --------------------------------------------------
            dt = abs((p_time - o_time).total_seconds())
            if dt > TIME_TOLERANCE_SEC:
                continue


            horiz_dist = safe_geodesic_meters(
                plat, plon,
                o_wp["Latitude"],
                o_wp["Longitude"]
            )

            alt_diff = abs(palt - o_wp["Altitude"])
            dist_3d = math.sqrt(horiz_dist**2 + alt_diff**2)

            if dist_3d < min_distance_meters:
                violations.append((p_wp, o_wp, dist_3d))

    return violations
