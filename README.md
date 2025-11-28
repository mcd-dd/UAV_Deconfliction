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

### 📋 System Workflow

| 🧩 **Step** | 🛠️ **Action**                                               | 🔗 **Module / Function**                       |
| :---------: | ----------------------------------------------------------- | ---------------------------------------------- |
|     1️⃣      | **Ingest dataset** (Excel → DataFrame)                      | `data_ingestion.load_dataset()`                |
|     2️⃣      | **Normalize & validate columns**                            | `data_ingestion.validate_input_df()`           |
|     3️⃣      | **Interpolate trajectories (optional)**                     | `spatial_engine.interpolate_trajectory()`      |
|     4️⃣      | **Build KD-Tree index for all non-primary drones**          | `spatial_engine.build_spatial_index()`         |
|     5️⃣      | **Perform fast spatial candidate pruning**                  | `spatial_engine.spatial_candidates_kdtree()`   |
|     6️⃣      | **Compute precise 3D distances**                            | `spatial_engine.compute_3d_distance()`         |
|     7️⃣      | **Detect spatial conflicts**                                | `spatial_engine.spatial_check()`               |
|     8️⃣      | **Run temporal window scan (± time_window_sec)**            | `temporal_engine.temporal_check()`             |
|     9️⃣      | **Generate mission status** (“clear” / “conflict detected”) | `conflict_engine.query_mission_status()`       |
|     🔟      | **Display 2D trajectory + conflict map**                    | `visualization.plot_2d.plot_primary_mission()` |
|    1️⃣1️⃣     | **Render 4D animation (3D + time)**                         | `visualization.plot_4d.animate_4d()`           |
|    1️⃣2️⃣     | **Export mission report (optional)**                        | `export.save_report()`                         |

### 🧱 Technologies Used
- Python 3.10+
- MatPlotLib
- Pandas
- SciPy KDTree
