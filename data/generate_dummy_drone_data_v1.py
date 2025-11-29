"""
uav_dataset_generator.py

Generates realistic multi-UAV waypoint missions for simulation and conflict testing.
Now includes:
 - 25% spatial conflict drones
 - 25% temporal conflict drones
 - 25% altitude conflict drones
 - 25% safe drones
 - EACH drone has a different takeoff time inside global scheduling window
 - Smooth altitude + realistic curved spatial trajectories
"""

from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Tuple

import numpy as np
import pandas as pd


# ============================================================================
# CONFIGURATION PARAMETERS
# ============================================================================
NUM_DRONES = 100
WAYPOINTS_PER_DRONE = 25

GLOBAL_T_START = datetime(2025, 5, 24, 10, 0, 0)
GLOBAL_T_END   = datetime(2025, 5, 24, 10, 45, 0)

PRIMARY_ID = 1

START_LAT = 30.2500
START_LON = -119.9500

RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)


# ============================================================================
# SPLIT DRONES INTO 4 EQUAL GROUPS
# ============================================================================
drone_ids = list(range(1, NUM_DRONES + 1))
random.shuffle(drone_ids)

chunk = NUM_DRONES // 4

SPATIAL_CONFLICT_DRONES  = set(drone_ids[0:chunk])
TEMPORAL_CONFLICT_DRONES = set(drone_ids[chunk: 2*chunk])
ALTITUDE_CONFLICT_DRONES = set(drone_ids[2*chunk: 3*chunk])
SAFE_DRONES              = set(drone_ids[3*chunk: 4*chunk])

# Ensure primary starts in safe zone unless user wants otherwise
SAFE_DRONES.add(PRIMARY_ID)
if PRIMARY_ID in SPATIAL_CONFLICT_DRONES:
    SPATIAL_CONFLICT_DRONES.remove(PRIMARY_ID)
if PRIMARY_ID in TEMPORAL_CONFLICT_DRONES:
    TEMPORAL_CONFLICT_DRONES.remove(PRIMARY_ID)
if PRIMARY_ID in ALTITUDE_CONFLICT_DRONES:
    ALTITUDE_CONFLICT_DRONES.remove(PRIMARY_ID)


# ============================================================================
# ALTITUDE PROFILE GENERATOR
# ============================================================================
def generate_smooth_altitude(n: int) -> np.ndarray:
    """Generate takeoff → cruise → landing altitude profile."""
    t = np.linspace(0.0, 1.0, n)
    alt = np.zeros(n)

    # takeoff: 0-20%
    takeoff = (t <= 0.2)
    alt[takeoff] = 120.0 * (t[takeoff] / 0.2)

    # cruise: 20-80%
    cruise = (t > 0.2) & (t < 0.8)
    alt[cruise] = 120.0 + 5.0 * np.sin(t[cruise] * 6 * np.pi)

    # landing: 80-100%
    landing = (t >= 0.8)
    alt[landing] = 120.0 - 110.0 * ((t[landing] - 0.8) / 0.2)

    # small noise
    alt += np.random.normal(scale=0.6, size=n)
    return alt


# ============================================================================
# SPATIAL CURVE GENERATOR
# ============================================================================
def generate_random_curve(n: int, end_lat: float, end_lon: float) -> Tuple[np.ndarray, np.ndarray]:
    """Curved Bézier-like lat/lon path."""
    t = np.linspace(0.0, 1.0, n)

    mid_lat = START_LAT + np.random.uniform(-0.01, 0.01)
    mid_lon = START_LON + np.random.uniform(-0.01, 0.01)

    lat = (
        START_LAT*(1 - t)**2 +
        2*mid_lat*t*(1 - t) +
        end_lat*t**2 +
        0.0008*np.random.randn(n)
    )

    lon = (
        START_LON*(1 - t)**2 +
        2*mid_lon*t*(1 - t) +
        end_lon*t**2 +
        0.0008*np.random.randn(n)
    )

    return lat, lon


# ============================================================================
# UNIQUE TAKEOFF TIME ASSIGNMENT
# ============================================================================
def assign_takeoff_times(n: int) -> dict[int, datetime]:
    """
    Assign each drone a unique takeoff time inside global window.
    """
    total_seconds = int((GLOBAL_T_END - GLOBAL_T_START).total_seconds())
    offsets = random.sample(range(0, total_seconds, 20), n)  # 20 sec spacing min
    offsets.sort()

    return {
        drone_ids[i]: GLOBAL_T_START + timedelta(seconds=offsets[i])
        for i in range(n)
    }


TAKEOFF_TIMES = assign_takeoff_times(NUM_DRONES)

# Replace existing generate_uav_dataset() and script block with the below

def generate_uav_dataset() -> pd.DataFrame:
    """
    Generate multi-UAV dataset with intended conflict groups.

    SAFE drones are guaranteed to start *after* GLOBAL_T_END + SAFE_BUFFER_MIN,
    so they will not temporally overlap with primary (or temporal-conflict) drones.
    """
    SAFE_BUFFER_MIN = 5  # minutes after GLOBAL_T_END before any SAFE drone starts
    records = []

    # Precompute a small per-drone offset for safe drones (seconds)
    safe_offsets_seconds = {}
    safe_list = sorted(list(SAFE_DRONES))
    for i, did in enumerate(safe_list):
        # stagger safe drones by 30s each so they don't overlap with each other
        safe_offsets_seconds[did] = i * 30

    for drone_id in drone_ids:
        # --------------------- SPATIAL ENDPOINT SELECTION ------------------
        end_lat = START_LAT + np.random.uniform(0.03, 0.15)
        end_lon = START_LON + np.random.uniform(0.03, 0.15)

        if drone_id in SPATIAL_CONFLICT_DRONES:
            end_lat = START_LAT + 0.04 + np.random.uniform(-0.0003, 0.0003)
            end_lon = START_LON + 0.04 + np.random.uniform(-0.0003, 0.0003)

        # --------------------- SPATIAL + ALTITUDE CURVES -------------------
        lat_curve, lon_curve = generate_random_curve(WAYPOINTS_PER_DRONE, end_lat, end_lon)
        alt_curve = generate_smooth_altitude(WAYPOINTS_PER_DRONE)

        # Altitude conflict drones → match primary cruise band
        if drone_id in ALTITUDE_CONFLICT_DRONES:
            alt_curve = 120.0 + np.random.uniform(-1.5, 1.5, WAYPOINTS_PER_DRONE)

        # --------------------- TIMESTAMP GENERATION -------------------------
        takeoff = TAKEOFF_TIMES[drone_id]

        for i in range(WAYPOINTS_PER_DRONE):

            # Primary timeline = baseline linear (mission window inside GLOBAL_T_START..GLOBAL_T_END)
            if drone_id == PRIMARY_ID:
                timestamp = GLOBAL_T_START + timedelta(seconds=i * 30)

            # Temporal conflict drones use same timestamps as primary
            elif drone_id in TEMPORAL_CONFLICT_DRONES:
                timestamp = GLOBAL_T_START + timedelta(seconds=i * 30)

            # SAFE drones: schedule entirely AFTER the mission window
            elif drone_id in SAFE_DRONES:
                safe_start = GLOBAL_T_END + timedelta(minutes=SAFE_BUFFER_MIN)
                # add small per-drone offset (staggering) and per-waypoint spacing
                offset_sec = safe_offsets_seconds.get(drone_id, 0)
                timestamp = safe_start + timedelta(seconds=offset_sec + i * 45)

            else:
                # Normal drones have jittered timeline relative to their assigned takeoff
                timestamp = takeoff + timedelta(seconds=i * 30 + random.randint(-8, 12))

            records.append([
                drone_id,
                timestamp,
                float(lat_curve[i]),
                float(lon_curve[i]),
                float(alt_curve[i]),
            ])

    df = pd.DataFrame(records, columns=["DroneID", "Time", "Latitude", "Longitude", "Altitude"])
    df["Time"] = pd.to_datetime(df["Time"])
    return df


# -----------------------
# Script entry (replace existing)
# -----------------------
if __name__ == "__main__":
    df = generate_uav_dataset()
    out_file = "100_drones_conflict_and_safe_fix_v2.xlsx"
    df.to_excel(out_file, index=False)

    print(f"\n✔ Dataset written: {out_file}")
    print(f" - Time window: {df['Time'].min()} → {df['Time'].max()}")
    print(f" - Spatial conflicts : {len(SPATIAL_CONFLICT_DRONES)} drones")
    print(f" - Temporal conflicts: {len(TEMPORAL_CONFLICT_DRONES)} drones")
    print(f" - Altitude conflicts: {len(ALTITUDE_CONFLICT_DRONES)} drones")
    print(f" - Safe drones       : {len(SAFE_DRONES)} drones\n")

    print("Summary groups:")
    print("Spatial:", sorted(list(SPATIAL_CONFLICT_DRONES)))
    print("Temporal:", sorted(list(TEMPORAL_CONFLICT_DRONES)))
    print("Altitude:", sorted(list(ALTITUDE_CONFLICT_DRONES)))
    print("Safe:", sorted(list(SAFE_DRONES)))

    # Quick verification: make sure SAFE drones do not overlap primary within tolerance
    def report_overlaps(primary_id: int, df: pd.DataFrame, tol_sec: int = 5):
        print('Primary ID:', primary_id)
        primary_times = set(df[df["DroneID"] == primary_id]["Time"].astype("datetime64[ns]"))
        safe_drones = sorted([d for d in SAFE_DRONES if d != primary_id])  # <-- FIX
        overlaps = []

        for sd in safe_drones:
            for t in df[df["DroneID"] == sd]["Time"]:
                if any(abs((pt - t).total_seconds()) <= tol_sec for pt in primary_times):
                    overlaps.append((sd, t))

        if overlaps:
            print("\n⚠ Overlaps detected between SAFE drones and primary within tolerance:")
            for sd, t in overlaps[:10]:
                print(sd, t)
        else:
            print(f"\n✔ No SAFE drone overlaps primary within ±{tol_sec} seconds.")

    def report_safe_drone_conflicts(df: pd.DataFrame, tol_sec: int = 5):
        """
        Check whether SAFE drones have conflicts with ANY other drone.
        - Time overlap check ± tol_sec
        """
        print("\n================ SAFE DRONE CONFLICT CHECK ================\n")

        safe_drones = sorted(list(SAFE_DRONES))
        all_drones = sorted(df["DroneID"].unique())

        # Pre-cache times for speed
        drone_times = {
            d: list(df[df["DroneID"] == d]["Time"].astype("datetime64[ns]"))
            for d in all_drones
        }

        conflicts = []   # (safe_drone, other_drone, time)

        for sd in safe_drones:
            sd_times = drone_times[sd]

            for od in all_drones:
                if od == sd:
                    continue  # skip self

                od_times = drone_times[od]

                # Compare times
                for t1 in sd_times:
                    for t2 in od_times:
                        if abs((t1 - t2).total_seconds()) <= tol_sec:
                            conflicts.append((sd, od, t1))
                            break  # break inner loop to avoid spam
                    else:
                        continue
                    break  # break mid-level loop when a conflict found

        if conflicts:
            print("⚠ SAFE DRONE TIME CONFLICTS DETECTED (should NOT happen):")
            conflicts = sorted(conflicts)

            for sd, od, t in conflicts[:20]:
                print(f"SAFE {sd} overlaps with Drone {od} @ {t}")

            if len(conflicts) > 20:
                print(f"... and {len(conflicts) - 20} more")
        else:
            print(f"✔ All SAFE drones are isolated in time (±{tol_sec} sec).")

        print("\n===========================================================\n")

