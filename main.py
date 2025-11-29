# main.py

import argparse
import sys
import pandas as pd

from ingestion.loader import load_waypoints_from_excel
from engine.conflict_engine import query_mission_status
from visualization.plot_2d import (
    plot_primary_mission,
    plot_all_trajectories,
    folium_visualize_mission,
)
from visualization.plot_4d import animate_4d


# Default parameters
DEFAULT_MIN_DISTANCE = 10.0
DEFAULT_PRIMARY_ID = 1001
DEFAULT_TIME_WINDOW = 1.0
DEFAULT_INTERP_STEP = 0.5


def main():
    """Entry point for the UAV Strategic Deconfliction CLI tool."""
    parser = argparse.ArgumentParser(
        description="UAV Strategic Deconfliction - modular"
    )

    parser.add_argument("excel_file", help="Path to Excel waypoint file")

    parser.add_argument(
        "--min-distance",
        type=float,
        default=DEFAULT_MIN_DISTANCE,
        help="Minimum 3D separation (meters)",
    )
    parser.add_argument(
        "--time-window-sec",
        type=float,
        default=DEFAULT_TIME_WINDOW,
        help="Temporal window (seconds)",
    )
    parser.add_argument(
        "--interp-step-sec",
        type=float,
        default=DEFAULT_INTERP_STEP,
        help="Interpolation step size (seconds)",
    )
    parser.add_argument(
        "--plot-2d",
        action="store_true",
        help="Show Matplotlib 2D plots",
    )
    parser.add_argument(
        "--plot-4d",
        action="store_true",
        help="Enable animated 4D visualization (Matplotlib)",
    )
    parser.add_argument(
        "--save-4d",
        type=str,
        default=None,
        help="File path to save 4D animation",
    )
    parser.add_argument(
        "--plot-folium",
        action="store_true",
        help="Render Folium map",
    )

    args = parser.parse_args()

    # -----------------------
    # Load dataset
    # -----------------------
    try:
        df = load_waypoints_from_excel(args.excel_file)
    except Exception as exc:
        print("Failed to load data:", exc, file=sys.stderr)
        sys.exit(2)

    # -----------------------
    # Interactive Loop
    # -----------------------
    while True:
        user_input = input("Enter Primary Drone ID (or 'quit'): ").strip()

        if user_input.lower() in ("quit", "exit"):
            print("Exiting interactive mode.")
            sys.exit(0)

        if not user_input.isdigit():
            print("❌ Invalid input. Enter a numeric Drone ID.\n")
            continue

        primary_id = int(user_input)

        print(f"\n🔍 Checking mission for Primary Drone {primary_id}...\n")

        result = query_mission_status(
            df,
            primary_id=primary_id,
            min_distance_meters=args.min_distance,
            time_window_sec=args.time_window_sec,
            interp_step_sec=args.interp_step_sec,
        )

        # -----------------------
        # Summary
        # -----------------------
        print("Status:", result["status"])
        print("Spatial Conflicts:", len(result["spatial_conflicts"]))
        print("Temporal Conflicts:", len(result["temporal_conflicts"]))

        # -----------------------
        # Detailed Output
        # -----------------------
        if result["status"] == "conflict detected":
            print("\n===============================")
            print("🚨 Mission Status: CONFLICT DETECTED")
            print("===============================\n")

            print(f"Spatial Violations: {len(result['spatial_conflicts'])}")
            for p_wp, o_wp, dist in result["spatial_conflicts"][:15]:
                print(
                    f"[Spatial] Primary@{p_wp[0]}  vs  "
                    f"Drone {o_wp['DroneID']} @ {o_wp['Time']}  → {dist:.2f} m"
                )

            print(f"\nTemporal Violations: {len(result['temporal_conflicts'])}")
            for p_wp, o_wp, dist in result["temporal_conflicts"][:15]:
                print(
                    f"[Temporal] Primary@{p_wp[0]}  vs  "
                    f"Drone {o_wp['DroneID']} @ {o_wp['Time']}  → {dist:.2f} m"
                )
        else:
            print("\n===============================")
            print("✔ Mission Status: CLEAR")
            print("===============================\n")

        print("Cleaning DataFrame to prevent mixed-type DroneID errors...")

        # -----------------------
        # Cleanup DataFrame
        # -----------------------
        df["DroneID"] = pd.to_numeric(df["DroneID"], errors="coerce")
        df = df.dropna(subset=["DroneID"])
        df["DroneID"] = df["DroneID"].astype(int)

        df["Time"] = pd.to_datetime(df["Time"], errors="coerce")
        df = df.dropna(subset=["Time"])

        for col in ["Latitude", "Longitude", "Altitude"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df = df.dropna(subset=[col])

        from visualization.plot_2d import _sanitize_conflicts

        spatial_conflicts = _sanitize_conflicts(result["spatial_conflicts"])
        temporal_conflicts = _sanitize_conflicts(result["temporal_conflicts"])

        # -----------------------
        # 2D Visualization
        # -----------------------
        if args.plot_2d:
            print("\n📊 Showing primary mission visualization...")
            plot_primary_mission(
                df,
                primary_id,
                spatial_conflicts,
                temporal_conflicts,
            )

            print("\n📊 Showing Trajectory of simulated drones...")
            plot_all_trajectories(
                df,
                primary_id,
                result["spatial_conflicts"],
                result["temporal_conflicts"],
            )

            if args.plot_folium:
                folium_visualize_mission(
                    df,
                    primary_id=primary_id,
                    spatial_conflicts=spatial_conflicts,
                    temporal_conflicts=temporal_conflicts,
                    batch_size=100,
                    page=1,
                    save_path="output/mission_map.html",
                )

        # -----------------------
        # 4D Animation
        # -----------------------
        if args.plot_4d or args.save_4d:
            animate_4d(
                df,
                result["spatial_conflicts"],
                result["temporal_conflicts"],
                primary_id,
                save_path=args.save_4d,
            )


if __name__ == "__main__":
    main()
