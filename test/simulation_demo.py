# visualization/simulation_demo.py
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import pandas as pd
import matplotlib.dates as mdates
from datetime import timedelta

# -----------------------------------------------------------
# 1) UTILITY — Generate Synthetic Missions
# -----------------------------------------------------------

def generate_scenario(conflict=True):
    """
    Generates:
    - primary mission
    - other drone path
    - scenarios: conflict-free or with conflict
    """

    start = pd.Timestamp("2025-05-24 10:00:00")

    # Primary drone path (straight line)
    t = np.array([start + timedelta(seconds=i * 5) for i in range(20)])
    lat_p = np.linspace(18.52, 18.58, len(t))
    lon_p = np.linspace(73.85, 73.90, len(t))
    alt_p = np.linspace(50, 120, len(t))

    primary = pd.DataFrame({
        "DroneID": 1001,
        "Time": t,
        "Latitude": lat_p,
        "Longitude": lon_p,
        "Altitude": alt_p
    })

    # Other drone path
    if conflict:
        # Intersecting path → guaranteed conflict
        lat_o = np.linspace(18.58, 18.52, len(t))
        lon_o = np.linspace(73.90, 73.85, len(t))
        alt_o = np.linspace(120, 50, len(t))
    else:
        # Offset path → no conflict
        lat_o = np.linspace(18.60, 18.62, len(t))
        lon_o = np.linspace(73.95, 73.98, len(t))
        alt_o = np.linspace(80, 100, len(t))

    other = pd.DataFrame({
        "DroneID": 2025,
        "Time": t,
        "Latitude": lat_o,
        "Longitude": lon_o,
        "Altitude": alt_o
    })

    df = pd.concat([primary, other], ignore_index=True)
    df.sort_values("Time", inplace=True)

    return df, primary, other


# -----------------------------------------------------------
# 2) STATIC VISUALIZATION — 2D Spatial + Temporal
# -----------------------------------------------------------

def plot_scenario(df, primary_id, spatial_conflicts, temporal_conflicts, save_path=None):
    """
    Plots:
    - Full spatial view
    - Temporal altitude view
    - Conflict highlights
    """

    primary = df[df["DroneID"] == primary_id]

    fig, axs = plt.subplots(1, 2, figsize=(14, 6))

    # ---------------- Spatial Plot ----------------
    axs[0].set_title("Spatial Flight Paths (Lat vs Lon)")
    axs[0].set_xlabel("Longitude")
    axs[0].set_ylabel("Latitude")

    # Plot all
    for drone_id in df["DroneID"].unique():
        d = df[df["DroneID"] == drone_id]
        axs[0].plot(d["Longitude"], d["Latitude"], label=f"Drone {drone_id}")

    # Conflicts
    for p, o, dist in spatial_conflicts:
        axs[0].scatter(o["Longitude"], o["Latitude"], c="red", s=30)

    axs[0].legend()

    # ---------------- Temporal Plot ----------------
    axs[1].set_title("Altitude vs Time")
    axs[1].set_xlabel("Time")
    axs[1].set_ylabel("Altitude (m)")

    for drone_id in df["DroneID"].unique():
        d = df[df["DroneID"] == drone_id]
        axs[1].plot(d["Time"], d["Altitude"], label=f"Drone {drone_id}")

    for p, o, dist in temporal_conflicts:
        axs[1].scatter(o["Time"], o["Altitude"], c="red", s=40)

    axs[1].xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
    axs[1].legend()

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=180)
    else:
        plt.show()


# -----------------------------------------------------------
# 3) ANIMATION — 4D (3D + Time)
# -----------------------------------------------------------

def animate_scenario(df, primary_id, spatial_conflicts, temporal_conflicts, save_path="scenario.mp4"):
    """
    Produces 4D animation:
    - 3D path
    - Time-evolving positions
    - Conflict points highlighted
    """

    from mpl_toolkits.mplot3d import Axes3D

    times = sorted(df["Time"].unique())
    drones = {d: g.sort_values("Time") for d, g in df.groupby("DroneID")}

    conflict_lookup = set()
    for p, o, d in spatial_conflicts + temporal_conflicts:
        conflict_lookup.add((o["Time"], o["Latitude"], o["Longitude"], o["Altitude"]))
        conflict_lookup.add((p[0], p[1], p[2], p[3]))

    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")

    scatters = {}
    for drone_id in drones:
        scatters[drone_id] = ax.plot([], [], [], marker="o", linestyle="None")[0]

    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_zlabel("Altitude")

    def update(i):
        t = times[i]
        ax.set_title(str(t))

        for drone_id, data in drones.items():
            row = data[data["Time"] == t]
            if row.empty:
                continue

            lon = row["Longitude"].values[0]
            lat = row["Latitude"].values[0]
            alt = row["Altitude"].values[0]

            is_conflict = (t, lat, lon, alt) in conflict_lookup

            scatters[drone_id]._offsets3d = ([lon], [lat], [alt])
            scatters[drone_id].set_color("red" if is_conflict else ("blue" if drone_id == primary_id else "gray"))
            scatters[drone_id].set_markersize(10 if is_conflict else 5)

        return scatters.values()

    ani = FuncAnimation(fig, update, frames=len(times), interval=200)

    ani.save(save_path, fps=5)
    plt.close()

