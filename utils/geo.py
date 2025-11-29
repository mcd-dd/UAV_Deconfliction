"""
Utility functions for geographic distance calculations.

This module provides:
- A pure-Python Haversine implementation (fast, reliable).
- A safe wrapper around geopy.distance.geodesic, with fallback to Haversine
  in case the geopy model fails due to bad inputs or environment issues.
"""

import math
from geopy.distance import geodesic


def haversine_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute the great-circle distance between two points on Earth (in meters)
    using the Haversine formula.

    Parameters
    ----------
    lat1, lon1 : float
        Latitude and longitude of the first point.
    lat2, lon2 : float
        Latitude and longitude of the second point.

    Returns
    -------
    float
        Distance between the two geographic coordinates in meters.
    """
    radius_earth_m = 6_371_000.0  # Earth radius in meters

    # Convert degrees → radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    # Haversine formula
    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1)
        * math.cos(phi2)
        * math.sin(delta_lambda / 2.0) ** 2
    )

    # Distance = 2R * arcsin(sqrt(a))
    return 2.0 * radius_earth_m * math.asin(math.sqrt(a))


def safe_geodesic_meters(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Compute the geodesic distance between two points using geopy,
    with automatic fallback to the Haversine method if geopy fails.

    This prevents runtime crashes when:
    - geopy encounters invalid coordinates
    - environment lacks geographic models
    - geodesic calculations fail due to internal exceptions

    Parameters
    ----------
    lat1, lon1 : float
        Latitude/longitude of first point.
    lat2, lon2 : float
        Latitude/longitude of second point.

    Returns
    -------
    float
        Distance between points in meters (geodesic or Haversine fallback).
    """
    try:
        # geopy.geodesic is accurate but sometimes fails
        return geodesic((lat1, lon1), (lat2, lon2)).meters
    except Exception:
        # Fallback ensures robustness
        return haversine_meters(lat1, lon1, lat2, lon2)
