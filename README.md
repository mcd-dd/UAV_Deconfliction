# 🛰️ UAV Strategic Deconfliction System
This project implements a strategic pre-flight deconfliction engine for drone (UAV) missions. It ingests drone waypoint data, performs high-performance spatial and temporal conflict checks, interpolates trajectories for smoother detection, and includes visualization tools (2D + 4D animation).

The system is designed for scalable, modular analysis of hundreds to thousands of drones.
---

## 🚀 Features

### 🧭 Data Ingestion
- Reads Excel or CSV waypoint data.
- Validates required columns.
- Normalizes timestamps.
- Converts numeric fields

### 📡 Conflict Engine
Uses:
- Trajectory interpolation
- KD-Tree spatial pruning (scipy.cKDTree)
- Windowed temporal checks
- 3D distance computation (horizontal + altitude)

### 🌍 Visualization
- 2D map plot: trajectories + conflict highlights.
- 2D time-altitude plot.
- 4D animation (3D + time), with conflict points in red.
- Optional MP4 export

### 🧠 Safety & Adaptability
- **Autonomous Return-to-Home (RTH)** and safe landing on mission completion or abort.
- Automatic synchronization between Mission and Drone states:  
  `available → in_mission → completed / aborted`
- Modular backend design — compatible with **SITL or real drones** via MAVLink.

---

## 🏗️ Directory Structure
```
uav_deconfliction/
│
├─ main.py
├─ requirements.txt
├─ README.md
├─ docs/
│   └─ reflection_justification.md
│
├─ src/
│   ├─ data_ingestion.py
│   ├─ spatial_check.py
│   ├─ temporal_check.py
│   ├─ conflict_engine.py
│   └─ utils.py
│
├─ visualization/
│   ├─ plot_2d.py
│   └─ plot_4d.py
│
└─ tests/
    └─ test_conflict_engine.py
```

---

## ⚙️ Core Components**

### 1️⃣ Backend (FastAPI)
- Provides RESTful endpoints for:
  - `/drones`, `/surveys`, `/flightpaths`, `/waypoints`, `/missions`, `/telemetry`
- Manages mission lifecycle via:
  
  POST /missions/start → Launch mission
  POST /missions/pause → Pause mission
  POST /missions/resume → Resume mission
  POST /missions/abort → Abort mission safely
  POST /missions/complete_by_drone → Mark mission complete

- Integrates with **DroneKit** for MAVLink-based UAV control.
- Launches **SITL + MAVProxy** subprocesses per mission with unique port assignments.

### 2️⃣ Mission Runner
- Threaded controller per drone:
  - Connection retry and timeout logic.
  - Arming, takeoff, waypoint traversal.
  - Real-time telemetry streaming.
  - Return-to-home and auto-landing behavior.
- Maintains mission state integrity:  
  `planned → in_progress → completed / aborted`

### 3️⃣ Frontend (Streamlit)
- Unified UI with four main dashboards:
- 🛰 **Mission Planner** — Create and assign surveys, paths, and drones  
- 🚁 **Fleet Visualization** — Monitor drone availability and battery  
- 📡 **Mission Monitoring** — Real-time telemetry + 3D visualization  
- 📊 **Survey Analytics Portal** — Summarized reports and charts
- Uses **PyDeck (Mapbox)** for 3D visualization and **Folium** for waypoint editing.

---

## 🧩 Installation

### Prerequisites
- Python ≥ 3.10  

### Steps
  ```bash
  # 1. Clone repository
  git clone https://github.com/your-username/uav_deconfliction.git
  cd uav_deconfliction
  
  # 2. Install dependencies
  pip install -r requirements.txt
  
  # 3. Run
  python3 main.py data/1000_drones.xlsx \
      --primary-id 1001 \
      --min-distance 10 \
      --time-window-sec 1 \
      --interp-step-sec 0.5 \
      --plot-2d \
      --plot-4d \
      --save-4d output.mp4
 _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ 
| Flag                | Description                          |
| ------------------- | ------------------------------------ |
| `--primary-id`      | Primary mission drone                |
| `--min-distance`    | Safe distance threshold              |
| `--time-window-sec` | Temporal conflict window (± seconds) |
| `--interp-step-sec` | Interpolation step size              |
| `--plot-2d`         | Show 2D visualization                |
| `--plot-4d`         | Run 4D animation                     |
| `--save-4d <file>`  | Save 4D animation to video           |

  ```
  ---

## 🕹 Usage Guide

### 🧭 Mission Planning

1. Create and manage **drones**, **surveys**, **flight paths**, and **waypoints** using the interactive Streamlit dashboard.  
2. Use **Folium maps** for waypoint definition and spatial visualization.  
3. Assign **Flight Paths** to specific Drones for mission scheduling and management.  

---

### 📡 Mission Execution

1. Open the **📡 Mission Monitoring** tab from the dashboard.  
2. Start missions for selected drones and monitor **position**, **progress**, and **battery** in real time.  
3. Pause, resume, or abort missions as needed during flight.  
4. Upon completion, drones **automatically return home** for safe landing.  

---

## 🔒 Safety & Fault Tolerance

### 1️⃣ Collision Avoidance System

Real-time proximity detection prevents drone collisions.  
If two drones approach within a **10 m safety radius**, automatic **pause** is triggered for involved drones.  
Alerts are logged, and optional dashboard notifications are generated.  

**In-flight safety layers:**
- 🛫 **Pre-Takeoff Check** — Ensures clear airspace before arming.  
- ✈️ **Dynamic Altitude Offsets** — Auto-adjusts (+5 m) when another drone is nearby.  
- 🛬 **Safe Landing Queue** — Sequential descent to prevent simultaneous landings.  

---

### 2️⃣ State Safety

Automatic drone-state reset (`available`) occurs after mission completion or abort.  
The backend ensures no concurrent missions are assigned to the same drone.  

---

### 3️⃣ Auto Recovery

On backend startup, any drone stuck in the `in_mission` state is **automatically reset**.  
This guarantees reliability and mission continuity after server restarts or system failures.  

---

### 4️⃣ Connection Handling

`MissionController` retries **SITL/MAVLink** connections up to **5 times**.  
Connection failures are handled gracefully without disrupting other missions.  

---

### 5️⃣ Telemetry Reliability

Continuous telemetry streams provide real-time updates for **GPS**, **altitude**, **battery**, **progress**, and **ETA**.  
All errors are logged safely, ensuring ongoing mission stability.  

---

## 🔄 Adaptability

### 🔁 SITL → Real Drone Transition
- SITL → Real Drone Transition:
  Replace SITL connection (tcp:127.0.0.1:5760) with your drone’s MAVLink UDP endpoint (udp:192.168.x.x:14550).
- Extensible Control Logic:
  Extend MissionController for swarm coordination, AI route re-planning, or safety analytics.
- API-First Design:
  Compatible with external ground stations or dashboards.

### 📋 Example Workflow

| 🧩 Step | 🪶 Action | 🔗 API / Module |
|:-------:|-----------|----------------|
| 1️⃣ | Add drone to system | `/drones` |
| 2️⃣ | Define survey + flight path | `/surveys`, `/flightpaths` |
| 3️⃣ | Add waypoints | `/flightpaths/{id}/waypoints` |
| 4️⃣ | Assign mission | `/missions/assign` |
| 5️⃣ | Start mission | `/missions/start` |
| 6️⃣ | Track progress | `/telemetry` |
| 7️⃣ | Complete mission | `/missions/complete_by_drone` |

### 🧱 Technologies Used
- Python 3.10+
- FastAPI (Backend REST API)
- Streamlit (Frontend Dashboard)
- DroneKit-Python (MAVLink control)
- ArduPilot SITL (Simulation)
    • 
