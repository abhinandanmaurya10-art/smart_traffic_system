import pytest

from logic import calculate_green_time, RoadState, calculate_priority_score, choose_road, fixed_time_choice
from config import MIN_GREEN_TIME, MAX_GREEN_TIME


def test_calculate_green_time_bounds():
    assert calculate_green_time(0) >= MIN_GREEN_TIME
    assert calculate_green_time(1000) <= MAX_GREEN_TIME


def test_priority_scoring_and_choice_starvation():
    # setup states
    s = {
        "A": RoadState(vehicle_count=5, wait_cycles=0, pedestrian_request=False),
        "B": RoadState(vehicle_count=3, wait_cycles=5, pedestrian_request=False),
    }
    # B has high wait_cycles so should be chosen due to starvation
    chosen = choose_road(s, {"vehicle_count": 1.0, "waiting_time": 0.0, "pedestrian": 0.0})
    assert chosen == "B"


def test_fixed_time_cycle():
    states = {"North": RoadState(), "South": RoadState(), "East": RoadState()}
    # sequential choices
    first = fixed_time_choice(states, -1)
    second = fixed_time_choice(states, list(states.keys()).index(first))
    assert first in states
    assert second in states
