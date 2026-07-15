"""Configuration constants for Adaptive Smart Traffic Signal System."""
from typing import Dict

# Roads
ROADS = ["North", "South", "East", "West"]

# Timings (seconds)
MIN_GREEN_TIME = 5
MAX_GREEN_TIME = 30
YELLOW_TIME = 3
ALL_RED_GAP = 1
EMERGENCY_GREEN_TIME = 15

# Priority scoring weights (default)
WEIGHTS: Dict[str, float] = {
    "vehicle_count": 1.0,  # w1
    "waiting_time": 0.5,    # w2
    "pedestrian": 2.0,      # w3
}

# Starvation prevention
MAX_WAIT_CYCLES = 3

# Pedestrian constraints
MAX_PEDESTRIAN_WAIT_CYCLES = 4

# Visualization / UI
LIGHT_COLORS = {
    "green": "#2ecc71",
    "yellow": "#f1c40f",
    "red": "#e74c3c",
}

BULB_ON = {"red": "#ff2b2b", "yellow": "#ffd83b", "green": "#2ecc71"}
BULB_OFF = {"red": "#4a1414", "yellow": "#4a4014", "green": "#123d22"}

# Safety clamps
MIN_VEHICLE_COUNT = 0
MAX_VEHICLE_COUNT = 100

# Random traffic generation bounds
RANDOM_MIN = 0
RANDOM_MAX = 40
