# Adaptive Smart Traffic Signal System

This project is an interview-ready, portfolio-grade Streamlit app that simulates an adaptive traffic signal controller with starvation prevention, pedestrian requests, emergency override, and a fixed-time baseline for comparison.

How to run
=========

1. Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Run the Streamlit app:

```powershell
streamlit run app.py
```

Design Decisions
================

- Priority scoring formula: `score = w1*vehicle_count + w2*waiting_time + w3*pedestrian_flag`.
- Starvation prevention: if a road's `wait_cycles` exceeds `MAX_WAIT_CYCLES` it is forced green (aging).
- Emergency override: per-road emergency flag forces immediate green for a fixed duration, then clears.
- Fixed-time baseline: simple round-robin scheduler used for side-by-side comparison with Adaptive.

Files
=====

- `app.py` — Streamlit entrypoint wiring UI, modes, and charts.
- `logic.py` — Pure functions and `RoadState` dataclass for scheduling logic.
- `ui_components.py` — Rendering helpers (traffic bulbs, junction layout).
- `config.py` — Constants and default weights.
- `tests/` — Pytest unit tests for core logic.
- `requirements.txt` — Dependencies.

Results (sample)
================

- Typical runs demonstrate improved throughput and lower average wait cycles versus fixed-time baseline. See the in-app Comparison table and throughput chart.

Notes
=====

- We kept the original visual style and timer display, enhancing the algorithm and structure.
- The weights and starvation limit are adjustable via the sidebar `Advanced` settings for demoability.

Demo
=====
Live Link: https://smarttrafficsystem-ycqjmsniqlk9kt43nwp8pr.streamlit.app/
