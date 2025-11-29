"""
2D Visualization Utilities for UAV Strategic Deconfliction
==========================================================

This module contains:
    - Plotting of the primary UAV mission
    - Plotting all UAV trajectories (spatial + altitude views)
    - Conflict visualization (spatial + temporal)
    - Folium-based interactive map generation with pagination

Key Features:
    ✓ Efficient plotting for 100–500 drones
    ✓ Downsampling for performance
    ✓ Time normalization for stable altitude plots
    ✓ Spatial & temporal conflict overlays
    ✓ Paginated folium maps (100 drones per page)
"""

# from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from typing import List, Tuple

"""
Interactive Folium Map Visualization for UAV Fleets
====================================================

Creates interactive HTML maps for large numbers of UAVs.
Supports:
    ✓ Paginated display (100 drones at a time)
    ✓ Always includes primary drone
    ✓ Spatial + temporal conflict markers
    ✓ Start/End markers for primary UAV

Designed for large datasets (100-2000 drones).
"""


import folium
import pandas as pd
from folium.plugins import PolyLineTextPath
from typing import List, Tuple

def folium_visualize_mission(
    df: pd.DataFrame,
    primary_id: int,
    spatial_conflicts: List[Tuple],
    temporal_conflicts: List[Tuple],
    save_path: str = "mission_map.html",
    batch_size: int = 100,
    page: int = 1
) -> folium.Map:
    """
    Render a paginated Folium map containing drone trajectories, with clear
    visual distinction between spatial and temporal conflict markers.
    """

 # -----------------------------
    # PAGINATION
    # -----------------------------
    all_drones = sorted(df["DroneID"].unique())

    if primary_id in all_drones:
        all_drones.remove(primary_id)

    chunks = [
        all_drones[i:i + batch_size]
        for i in range(0, len(all_drones), batch_size)
    ]

    if not chunks:
        chunks = [[]]

    page_idx = max(0, min(page - 1, len(chunks) - 1))
    selected_ids = [primary_id] + chunks[page_idx]

    print(
        f"\n📌 Showing drones {page_idx * batch_size + 1}-"
        f"{page_idx * batch_size + len(selected_ids) - 1}"
        f" of {len(all_drones) + 1}"
    )

    plot_df = df[df["DroneID"].isin(selected_ids)]

    center_lat = plot_df["Latitude"].mean()
    center_lon = plot_df["Longitude"].mean()

    # -----------------------------
    # BASE MAP
    # -----------------------------
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=13,
        tiles="OpenStreetMap"
    )

    # Colors
    PRIMARY_COLOR = "blue"
    OTHER_COLOR = "gray"
    SPATIAL_COLOR = "red"
    TEMPORAL_COLOR = "yellow"

    # -----------------------------
    # DRAW TRAJECTORIES
    # -----------------------------
    for drone_id in selected_ids:
        d = plot_df[plot_df["DroneID"] == drone_id].sort_values("Time")
        coords = list(zip(d["Latitude"], d["Longitude"]))

        if len(coords) < 2:
            continue

        color = PRIMARY_COLOR if drone_id == primary_id else OTHER_COLOR

        poly = folium.PolyLine(
            coords,
            color=color,
            weight=4 if drone_id == primary_id else 1.5,
            opacity=1.0 if drone_id == primary_id else 0.55,
            tooltip=f"Drone {drone_id}"
        ).add_to(m)

        # Label trajectory
        try:
            PolyLineTextPath(
                poly,
                f"{drone_id}",
                repeat=False,
                offset=10,
                attributes={"fill": color, "font-weight": "bold"},
            ).add_to(m)
        except Exception:
            pass

    # -----------------------------
    # MARK SPATIAL CONFLICTS (RED)
    # -----------------------------
    for p_wp, o_wp, dist in spatial_conflicts:
        if o_wp["DroneID"] not in selected_ids:
            continue

        folium.CircleMarker(
            location=[o_wp["Latitude"], o_wp["Longitude"]],
            radius=7,
            color=SPATIAL_COLOR,
            fill=True,
            fill_opacity=1.0,
            tooltip=(
                f"SPATIAL Conflict with Drone {o_wp['DroneID']} @ {o_wp['Time']} "
                f"({dist:.2f} m)"
            ),
        ).add_to(m)

    # -----------------------------
    # MARK TEMPORAL CONFLICTS (YELLOW)
    # -----------------------------
    for p_wp, o_wp, dist in temporal_conflicts:
        if o_wp["DroneID"] not in selected_ids:
            continue

        folium.CircleMarker(
            location=[o_wp['Latitude'], o_wp['Longitude']],
            radius=7,
            color=TEMPORAL_COLOR,
            fill=True,
            fill_opacity=1.0,
            tooltip=(
                f"TEMPORAL Conflict with Drone {o_wp['DroneID']} @ {o_wp['Time']} "
                f"({dist:.2f} m)"
            ),
        ).add_to(m)

    # -----------------------------
    # PRIMARY START/END MARKERS
    # -----------------------------
    primary_df = df[df["DroneID"] == primary_id].sort_values("Time")

    folium.Marker(
        [primary_df.iloc[0]["Latitude"], primary_df.iloc[0]["Longitude"]],
        popup="Primary Start",
        icon=folium.Icon(color="green", icon="play")
    ).add_to(m)

    folium.Marker(
        [primary_df.iloc[-1]["Latitude"], primary_df.iloc[-1]["Longitude"]],
        popup="Primary End",
        icon=folium.Icon(color="blue", icon="stop")
    ).add_to(m)

    # -----------------------------
    # ADD LEGEND
    # -----------------------------
    legend_html = """
        <div style="
            position: fixed;
            bottom: 40px;
            left: 40px;
            width: 210px;
            background-color: white;
            z-index:9999;
            font-size:14px;
            border:2px solid grey;
            padding: 10px;
        ">
        <b>Legend</b><br>
        <span style="color:blue;">■</span> Primary Drone<br>
        <span style="color:gray;">■</span> Other Drones<br>
        <span style="color:red;">●</span> Spatial Conflicts<br>
        <span style="color:gold;">●</span> Temporal Conflicts<br>
        <span style="color:green;">▲</span> Primary Start<br>
        <span style="color:blue;">▲</span> Primary End<br>
        </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # -----------------------------
    # SAVE & RETURN
    # -----------------------------
    m.save(save_path)
    print(f"🌍 Saved folium map: {save_path}")

    return m

def _sanitize_conflicts(conflicts):
    """
    Normalize and clean raw conflict records.

    This function ensures all conflict tuples follow the same format:

        (primary_wp, other_wp, distance)

    where:
        primary_wp : tuple
            (Time, Latitude, Longitude, Altitude)
        other_wp : dict
            {
                "DroneID": int,
                "Time": Timestamp,
                "Latitude": float,
                "Longitude": float,
                "Altitude": float
            }
        distance : float

    It also:
        - Converts malformed waypoints (lists/arrays) into proper types.
        - Assigns placeholder timestamps for missing time fields.
        - Ensures numeric fields are floats.
        - Removes nested NumPy arrays by flattening to scalar floats.

    Parameters
    ----------
    conflicts : list
        A list of tuples, each containing:
        (primary_wp, other_wp, distance)

    Returns
    -------
    list
        Cleaned list of sanitized conflict tuples.
    """
    import numpy as np
    import pandas as pd

    sanitized = []

    for primary_wp, other_wp, dist in conflicts:

        # --------------------------------------------------------
        # SANITIZE PRIMARY WAYPOINT
        # --------------------------------------------------------
        # Allow formats:
        #   [lat, lon, alt]  → no timestamp, fix needed
        #   [time, lat, lon, alt]
        if isinstance(primary_wp, (list, tuple, np.ndarray)):

            # Case: [lat, lon, alt] (missing timestamp)
            if len(primary_wp) == 3:
                primary_wp = (
                    pd.NaT,          # placeholder timestamp
                    float(primary_wp[0]),
                    float(primary_wp[1]),
                    float(primary_wp[2]),
                )

            # Case: [time, lat, lon, alt]
            elif len(primary_wp) == 4:
                primary_wp = (
                    primary_wp[0],
                    float(primary_wp[1]),
                    float(primary_wp[2]),
                    float(primary_wp[3]),
                )

            else:
                raise ValueError(
                    f"Malformed primary waypoint: {primary_wp}"
                )

        # --------------------------------------------------------
        # SANITIZE OTHER WAYPOINT
        # --------------------------------------------------------
        if isinstance(other_wp, dict):

            # Convert any lists/arrays to float scalars
            for key in ("Latitude", "Longitude", "Altitude"):
                if isinstance(other_wp.get(key), (list, np.ndarray)):
                    other_wp[key] = float(other_wp[key][0])

        elif isinstance(other_wp, (list, tuple, np.ndarray)):

            # Case: [lat, lon, alt]
            if len(other_wp) == 3:
                other_wp = {
                    "DroneID": -1,        # unknown
                    "Time": pd.NaT,
                    "Latitude": float(other_wp[0]),
                    "Longitude": float(other_wp[1]),
                    "Altitude": float(other_wp[2]),
                }
            else:
                raise ValueError(f"Malformed other waypoint: {other_wp}")

        else:
            raise ValueError(f"Invalid other_wp type: {type(other_wp)}")

        # --------------------------------------------------------
        # APPEND CLEANED RESULT
        # --------------------------------------------------------
        sanitized.append((primary_wp, other_wp, float(dist)))

    return sanitized

def plot_primary_mission(
    df: pd.DataFrame,
    primary_id: int,
    spatial_conflicts: List[Tuple],
    temporal_conflicts: List[Tuple],
) -> None:
    """
    Visualize the mission of the primary UAV with:
    
    Left subplot:
        - Full spatial plot (lat vs lon)
        - Primary trajectory emphasized in blue
        - Spatial conflict points marked in red

    Right subplot:
        - Altitude vs time profile
        - Temporal conflict points highlighted

    Parameters
    ----------
    df : pd.DataFrame
        DataFrame containing UAV waypoints with columns:
        ['DroneID', 'Time', 'Latitude', 'Longitude', 'Altitude']

    primary_id : int
        ID of the drone considered as the primary mission.

    spatial_conflicts : list of tuples
        List of (primary_wp, other_wp, distance) for spatial conflicts.

    temporal_conflicts : list of tuples
        List of (primary_wp, other_wp, distance) for temporal conflicts.
    """

    primary_df = df[df["DroneID"] == primary_id].sort_values("Time")

    fig, axs = plt.subplots(1, 2, figsize=(16, 7))

    # ================================================================
    # 1) SPATIAL VIEW
    # ================================================================
    ax = axs[0]
    ax.set_title(f"Primary Drone {primary_id} — Spatial Path")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    # All drones in background
    ax.scatter(
        df["Longitude"], df["Latitude"],
        s=6, alpha=0.15, color="lightgray",
        label="Other Drones (Background)"
    )

    # Primary trajectory
    ax.plot(
        primary_df["Longitude"],
        primary_df["Latitude"],
        color="blue", linewidth=2.5, marker="o", markersize=4,
        label="Primary Path"
    )

    # --- Spatial conflicts ---
    spatial_points_x = []
    spatial_points_y = []

    for p_wp, o_wp, dist in spatial_conflicts[:1500]:
        spatial_points_x.append(o_wp["Longitude"])
        spatial_points_y.append(o_wp["Latitude"])

        # Draw connecting line
        ax.plot(
            [p_wp[2], o_wp["Longitude"]],
            [p_wp[1], o_wp["Latitude"]],
            "r-", linewidth=1.0, alpha=0.7
        )

    # Add spatial markers once (for legend)
    if spatial_points_x:
        ax.scatter(
            spatial_points_x, spatial_points_y,
            s=40, color="red", marker="o",
            label="Spatial Conflict"
        )

    ax.legend(loc="lower right")

    # ================================================================
    # 2) ALTITUDE VS TIME VIEW
    # ================================================================
    ax = axs[1]
    ax.set_title(f"Primary Drone {primary_id} — Altitude Profile")
    ax.set_xlabel("Time")
    ax.set_ylabel("Altitude (m)")

    # Primary altitude profile
    ax.plot(
        primary_df["Time"],
        primary_df["Altitude"],
        color="blue", linewidth=2,
        marker="o", markersize=4,
        label="Primary Altitude"
    )

    # --- Temporal conflicts ---
    temporal_x = []
    temporal_y = []

    for p_wp, o_wp, dist in temporal_conflicts[:1500]:
        temporal_x.append(o_wp["Time"])
        temporal_y.append(o_wp["Altitude"])

        ax.plot(
            [p_wp[0], o_wp["Time"]],
            [p_wp[3], o_wp["Altitude"]],
            "r--", linewidth=1.0, alpha=0.7
        )

    if temporal_x:
        ax.scatter(
            temporal_x, temporal_y,
            s=50, color="red", marker="^",
            label="Temporal Conflict"
        )

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%H:%M:%S"))
    ax.legend(loc="upper right")

    plt.tight_layout()
    plt.show()

def plot_all_trajectories(
    df: pd.DataFrame,
    primary_id: int,
    spatial_conflicts: List[Tuple],
    temporal_conflicts: List[Tuple]
) -> None:
    """
    Plot spatial (Lat–Lon) and altitude (Time–Altitude) trajectories for
    ALL drones in the system.

    Features
    --------
    - Handles 100–500 drones efficiently
    - Downsampling improves performance
    - Avoids NaN/Inf axis errors
    - Marks spatial & temporal conflicts in red
    - Uses normalized time for stability

    Parameters
    ----------
    df : pd.DataFrame
        Waypoint records of all drones.

    primary_id : int
        ID of the mission-critical drone.

    spatial_conflicts : list
        List of (primary_wp, other_wp, distance) spatial conflicts.

    temporal_conflicts : list
        List of (primary_wp, other_wp, distance) temporal conflicts.
    """

    df = df.copy()
    df["Altitude"] = pd.to_numeric(df["Altitude"], errors="coerce")
    df = df.dropna(subset=["Altitude"])

    t0 = df["Time"].min()
    df["_tsec"] = (df["Time"] - t0).dt.total_seconds()

    fig, axs = plt.subplots(1, 2, figsize=(18, 7))

    # ================================================================
    # 1) SPATIAL PLOT
    # ================================================================
    ax = axs[0]
    ax.set_title("All Drone Trajectories (Spatial View)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")

    for drone_id, d in df.groupby("DroneID"):

        d = d.sort_values("Time")
        d_small = d.iloc[::10]

        if drone_id == primary_id:
            ax.plot(
                d_small["Longitude"], d_small["Latitude"],
                color="blue", linewidth=2.5, marker="o", markersize=3,
                label="Primary Path"
            )
        else:
            ax.plot(
                d_small["Longitude"], d_small["Latitude"],
                color="gray", linestyle="--",
                alpha=0.25, linewidth=0.7,
            )

    # Spatial conflict points
    spatial_x = [o_wp["Longitude"] for _, o_wp, _ in spatial_conflicts[:1000]]
    spatial_y = [o_wp["Latitude"] for _, o_wp, _ in spatial_conflicts[:1000]]

    if spatial_x:
        ax.scatter(
            spatial_x, spatial_y,
            color="red", s=30, marker="o",
            label="Spatial Conflict"
        )

    ax.legend(loc="lower right")

    # ================================================================
    # 2) ALTITUDE PROFILE
    # ================================================================
    ax = axs[1]
    ax.set_title("Drone Altitude Profiles (Time vs Altitude)")
    ax.set_xlabel("Time (sec)")
    ax.set_ylabel("Altitude (m)")

    valid_altitudes = []

    for drone_id, d in df.groupby("DroneID"):
        d = d.sort_values("Time")
        d_small = d.iloc[::10]

        if len(d_small) < 2:
            continue

        valid_altitudes.extend([d_small["Altitude"].min(), d_small["Altitude"].max()])

        if drone_id == primary_id:
            ax.plot(
                d_small["_tsec"], d_small["Altitude"],
                linewidth=2, color="blue", marker="o", markersize=4,
                label="Primary Altitude"
            )
        else:
            ax.plot(
                d_small["_tsec"], d_small["Altitude"],
                linewidth=0.6, color="gray",
                linestyle="--", alpha=0.3,
            )

    # Y-axis scaling
    if valid_altitudes:
        ymin, ymax = min(valid_altitudes), max(valid_altitudes)
        pad = max(5, (ymax - ymin) * 0.15)
        ax.set_ylim(ymin - pad, ymax + pad)

    # Temporal conflict markers
    temporal_t = [(o_wp["Time"] - t0).total_seconds() for _, o_wp, _ in temporal_conflicts[:1000]]
    temporal_alt = [o_wp["Altitude"] for _, o_wp, _ in temporal_conflicts[:1000]]

    if temporal_t:
        ax.scatter(
            temporal_t, temporal_alt,
            color="red", s=40, marker="^",
            label="Temporal Conflict"
        )

    ax.legend(loc="upper right")

    plt.tight_layout()
    plt.show()