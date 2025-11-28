# UAV Strategic Deconfliction System
Modular Python Project for Spatial + Temporal Drone Conflict Detection

📌 Overview

This project implements a strategic pre-flight deconfliction engine for drone (UAV) missions. It ingests drone waypoint data, performs high-performance spatial and temporal conflict checks, interpolates trajectories for smoother detection, and includes visualization tools (2D + 4D animation).

The system is designed for scalable, modular analysis of hundreds to thousands of drones.

🚀 Features
✔ Data Ingestion

Reads Excel or CSV waypoint data

Validates required columns

Normalizes timestamps

Converts numeric fields

✔ Conflict Engine (Optimized)

Uses:

Trajectory interpolation

KD-Tree spatial pruning (scipy.cKDTree)

Windowed temporal checks

3D distance computation (horizontal + altitude)

✔ Visualization

2D map plot: trajectories + conflict highlights

2D time-altitude plot

4D animation (3D + time), with conflict points in red

Optional MP4 export
