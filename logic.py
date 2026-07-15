"""Pure logic for the Adaptive Smart Traffic Signal System.
This module contains functions without Streamlit imports so it can be tested easily.
"""
from typing import Dict, Optional
from dataclasses import dataclass

import random

from config import (
    ROADS,
    MIN_GREEN_TIME,
    MAX_GREEN_TIME,
    WEIGHTS,
    MAX_WAIT_CYCLES,
    MIN_VEHICLE_COUNT,
    MAX_VEHICLE_COUNT,
    RANDOM_MIN,
    RANDOM_MAX,
    EMERGENCY_GREEN_TIME,
)


@dataclass
class RoadState:
    vehicle_count: int = 0
    wait_cycles: int = 0
    pedestrian_request: bool = False
    emergency: bool = False


def clamp_vehicle_count(count: int) -> int:
    """Clamp vehicle counts to configured safe bounds."""
    return max(MIN_VEHICLE_COUNT, min(count, MAX_VEHICLE_COUNT))


def calculate_green_time(vehicle_count: int) -> int:
    """Calculate green time based on vehicle count, clamped to min/max.

    Args:
        vehicle_count: number of waiting vehicles.
    Returns:
        Green time in seconds.
    """
    vehicle_count = clamp_vehicle_count(vehicle_count)
    green_time = MIN_GREEN_TIME + (vehicle_count // 2)
    green_time = max(MIN_GREEN_TIME, min(green_time, MAX_GREEN_TIME))
    return green_time


def calculate_priority_score(
    road_state: RoadState, weights: Dict[str, float]
) -> float:
    """Compute priority score for a road.

    priority_score = w1*vehicle_count + w2*waiting_time + w3*pedestrian_flag
    """
    vehicle_component = weights.get("vehicle_count", 1.0) * road_state.vehicle_count
    waiting_component = weights.get("waiting_time", 0.0) * road_state.wait_cycles
    pedestrian_component = (
        weights.get("pedestrian", 0.0) * (1.0 if road_state.pedestrian_request else 0.0)
    )

    return vehicle_component + waiting_component + pedestrian_component


def choose_road(
    states: Dict[str, RoadState], weights: Dict[str, float], max_wait_cycles: int = MAX_WAIT_CYCLES
) -> Optional[str]:
    """Choose the road with the highest priority score, respecting starvation and emergency.

    - Emergency roads override everything and are selected immediately (first found).
    - If a road has waited > MAX_WAIT_CYCLES, it is forced to front (aging).
    - Otherwise pick by highest priority score.

    Returns the chosen road name or None if no roads are present.
    """
    if not states:
        return None

    # Emergency override
    for name, st in states.items():
        if st.emergency:
            return name

    # Starvation prevention (forced selection)
    for name, st in states.items():
        if st.wait_cycles > max_wait_cycles:
            return name

    # Otherwise choose by computed score
    scores = {name: calculate_priority_score(st, weights) for name, st in states.items()}
    # If all scores are equal (e.g., all zeros), fallback to round-robin by min wait_cycles
    if len(set(scores.values())) == 1:
        # choose the road with max wait_cycles
        return max(states.keys(), key=lambda n: states[n].wait_cycles)

    return max(scores, key=scores.get)


def update_starvation_counters(states: Dict[str, RoadState], selected: str) -> None:
    """Update wait_cycles counters: increment for non-selected roads, reset for selected."""
    for name, st in states.items():
        if name == selected:
            st.wait_cycles = 0
            st.pedestrian_request = False  # serviced when road goes green
            st.emergency = False  # assume emergency cleared after service
        else:
            st.wait_cycles += 1


def new_traffic_reading() -> Dict[str, int]:
    """Generate a randomized new traffic reading for each road."""
    return {road: random.randint(RANDOM_MIN, RANDOM_MAX) for road in ROADS}


def fixed_time_choice(states: Dict[str, RoadState], last_index: int = -1) -> str:
    """Simple round-robin fixed-time scheduler.

    Chooses next road in order irrespective of counts. Returns the chosen road name.
    """
    roads = list(states.keys())
    if not roads:
        raise ValueError("No roads available for fixed-time scheduling")
    next_index = (last_index + 1) % len(roads)
    return roads[next_index]
