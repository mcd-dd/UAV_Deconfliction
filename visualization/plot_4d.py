"""
4D Visualization Module
-----------------------

Provides animated 3D trajectory visualization for large UAV fleets using Plotly.

Features:
    • 3D scatter animation over time (time = frames)
    • Conflict-aware coloring (red for conflicts, blue for primary, gray for others)
    • Supports 100–1000 drones efficiently
    • Optionally saves HTML animation
"""

from typing import List, Tuple, Optional
import pandas as pd
import plotly.graph_objects as go

def animate_4d(
    df: pd.DataFrame,
    spatial_conflicts: List[Tuple],
    temporal_conflicts: List[Tuple],
    primary_id: int,
    save_path: Optional[str] = None
) -> go.Figure:
    """
    Create a 4D animation for UAV trajectories using Plotly.

    The animation encodes:
        • x-axis  → Longitude
        • y-axis  → Latitude
        • z-axis  → Altitude
        • Frames  → Time (4th dimension)

    Conflict points are shown in RED.
    Primary drone frames are highlighted in BLUE.
    All other drones shown in GRAY.

    Parameters
    ----------
    df : pd.DataFrame
        Full trajectory dataset containing:
        ['DroneID', 'Time', 'Latitude', 'Longitude', 'Altitude']

    spatial_conflicts : list of tuples
        Output of spatial conflict detection:
        [(primary_wp, other_wp, distance), ...]

    temporal_conflicts : list of tuples
        Output of temporal conflict detection:
        [(primary_wp, other_wp, distance), ...]

    primary_id : int
        ID of the main drone to highlight.

    save_path : str or None, optional
        If provided:
            - If ends with ".html": save animation as HTML.
            - Else: automatically append ".html".

    Returns
    -------
    go.Figure
        Fully constructed Plotly animation figure.
    """

    # ------------------------------------------------------------
    # BUILD CONFLICT LOOKUP TABLE
    # ------------------------------------------------------------
    conflict_set = set()

    for p_wp, o_wp, _ in spatial_conflicts + temporal_conflicts:
        # Primary WP tuple
        conflict_set.add((p_wp[0], p_wp[1], p_wp[2], p_wp[3]))

        # Other drone WP dictionary
        conflict_set.add((
            o_wp["Time"],
            o_wp["Latitude"],
            o_wp["Longitude"],
            o_wp["Altitude"]
        ))

    # ------------------------------------------------------------
    # PREPARE TIME FRAMES
    # ------------------------------------------------------------
    times = sorted(df["Time"].unique())
    frames = []

    for t in times:
        frame_df = df[df["Time"] == t]

        colors = []
        sizes = []

        # Classify every UAV waypoint
        for _, row in frame_df.iterrows():
            wp_key = (
                row["Time"],
                row["Latitude"],
                row["Longitude"],
                row["Altitude"]
            )

            if wp_key in conflict_set:
                colors.append("red")
                sizes.append(9)
            elif row["DroneID"] == primary_id:
                colors.append("blue")
                sizes.append(7)
            else:
                colors.append("gray")
                sizes.append(4)

        frames.append(
            go.Frame(
                name=str(t),
                data=[
                    go.Scatter3d(
                        x=frame_df["Longitude"],
                        y=frame_df["Latitude"],
                        z=frame_df["Altitude"],
                        mode="markers",
                        marker=dict(size=sizes, color=colors),
                    )
                ]
            )
        )

    # ------------------------------------------------------------
    # INITIAL EMPTY FIGURE
    # ------------------------------------------------------------
    fig = go.Figure(
        data=[go.Scatter3d(mode="markers", x=[], y=[], z=[])],
        frames=frames
    )

    # ------------------------------------------------------------
    # CONFIGURE SCENE & PLAY CONTROLS
    # ------------------------------------------------------------
    fig.update_layout(
        title="4D UAV Fleet Animation",
        scene=dict(
            xaxis_title="Longitude",
            yaxis_title="Latitude",
            zaxis_title="Altitude"
        ),
        updatemenus=[
            {
                "type": "buttons",
                "buttons": [
                    {
                        "label": "Play",
                        "method": "animate",
                        "args": [
                            None,
                            {"frame": {"duration": 150}, "fromcurrent": True}
                        ]
                    }
                ]
            }
        ]
    )

    # ------------------------------------------------------------
    # SAVE IF REQUIRED
    # ------------------------------------------------------------
    if save_path:
        if not save_path.lower().endswith(".html"):
            save_path = save_path + ".html"

        fig.write_html(save_path)
        print(f"✔ Saved 4D animation to: {save_path}")

    return fig