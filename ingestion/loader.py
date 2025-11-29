"""
Data ingestion utilities for UAV mission and waypoint files.

This module loads waypoint data from Excel spreadsheets and ensures:
    • Column names are normalized.
    • Data types are validated and converted.
    • Missing or corrupt rows are safely removed.
    • Output is formatted consistently for downstream processing.

Expected output columns:
    ['DroneID', 'Time', 'Latitude', 'Longitude', 'Altitude']
"""

from __future__ import annotations

from typing import Optional
import pandas as pd
import numpy as np


# ---------------------------------------------------------------------------
# LOAD WAYPOINT DATA FROM EXCEL
# ---------------------------------------------------------------------------
def load_waypoints_from_excel(
    path: str,
    time_col: str = "Time"
) -> pd.DataFrame:
    """
    Load UAV waypoint data from an Excel file and normalize its structure.

    Parameters
    ----------
    path : str
        Path to an Excel file (.xlsx) containing waypoint data.

    time_col : str, default="Time"
        Name of the timestamp column in the file.
        If different from "Time", it will be renamed automatically.

    Expected Columns
    ----------------
    The input Excel file must provide at least these columns:
        • DroneID
        • <time_col>
        • Latitude
        • Longitude
        • Altitude

    Returns
    -------
    pandas.DataFrame
        Cleaned and normalized DataFrame with columns:
        ['DroneID', 'Time', 'Latitude', 'Longitude', 'Altitude']

    Raises
    ------
    ValueError
        If required columns are missing or unreadable.

    Notes
    -----
    • Non-numeric latitude/longitude/altitude values are coerced to NaN and dropped.
    • Timestamps are converted to pandas datetime.
    • Any row missing critical values is removed.
    """

    # --------------------------------------------------------------
    # 1. Load Excel file
    # --------------------------------------------------------------
    try:
        df = pd.read_excel(path, engine="openpyxl")
    except Exception as exc:
        raise ValueError(f"Failed to read Excel file: {path}\nError: {exc}")

    # Strip whitespace from column names
    df.columns = [str(c).strip() for c in df.columns]

    # --------------------------------------------------------------
    # 2. Validate required columns
    # --------------------------------------------------------------
    required_cols = {"DroneID", time_col, "Latitude", "Longitude", "Altitude"}
    missing = required_cols - set(df.columns)

    if missing:
        raise ValueError(
            f"Missing required columns in file '{path}': {missing}"
        )

    # --------------------------------------------------------------
    # 3. Convert timestamp column → datetime
    # --------------------------------------------------------------
    if not np.issubdtype(df[time_col].dtype, np.datetime64):
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce")

    # --------------------------------------------------------------
    # 4. Convert numeric columns
    # --------------------------------------------------------------
    for col in ["Latitude", "Longitude", "Altitude"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Rename time column if necessary
    if time_col != "Time":
        df = df.rename(columns={time_col: "Time"})

    # --------------------------------------------------------------
    # 5. Remove corrupted rows
    # --------------------------------------------------------------
    df = df.dropna(
        subset=["DroneID", "Time", "Latitude", "Longitude", "Altitude"]
    )

    # Ensure DroneID is int
    df["DroneID"] = df["DroneID"].astype(int)

    # Sort results by time (stable for consistency)
    df = df.sort_values(["DroneID", "Time"]).reset_index(drop=True)

    return df
