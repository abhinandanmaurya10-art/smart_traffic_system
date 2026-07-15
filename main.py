import random
import time
from typing import Dict

import pandas as pd
import streamlit as st

ROADS = ["North", "South", "East", "West"]

MIN_GREEN_TIME = 5
MAX_GREEN_TIME = 30
YELLOW_TIME = 3
ALL_RED_GAP = 1

LIGHT_COLORS = {
    "green": "#2ecc71",
    "yellow": "#f1c40f",
    "red": "#e74c3c",
}

BULB_ON = {"red": "#ff2b2b", "yellow": "#ffd83b", "green": "#2ecc71"}
BULB_OFF = {"red": "#4a1414", "yellow": "#4a4014", "green": "#123d22"}


st.set_page_config(page_title="Smart Traffic Signal System", page_icon="🚦", layout="centered")


def calculate_green_time(vehicle_count: int) -> int:
    """
    More waiting vehicles => longer green light.
    The result is always kept between MIN_GREEN_TIME and MAX_GREEN_TIME.
    """
    green_time = MIN_GREEN_TIME + (vehicle_count // 2)
    green_time = max(MIN_GREEN_TIME, min(green_time, MAX_GREEN_TIME))
    return green_time


def choose_road(vehicle_counts: Dict[str, int]) -> str:
    return max(vehicle_counts, key=vehicle_counts.get)


def new_traffic_reading() -> Dict[str, int]:
    return {road: random.randint(0, 40) for road in ROADS}


def bulb_html(bulb_color: str, is_on: bool) -> str:
    if is_on:
        bg = BULB_ON[bulb_color]
        style = (
            f"background:radial-gradient(circle at 35% 32%, #ffffffaa, {bg} 60%);"
            f"box-shadow:0 0 16px 5px {bg}aa;"
        )
    else:
        bg = BULB_OFF[bulb_color]
        style = f"background:{bg}; box-shadow:inset 0 0 6px rgba(0,0,0,0.6);"

    return (
        f"<div style='width:34px;height:34px;border-radius:50%;margin:5px auto;"
        f"border:2px solid #111;{style}'></div>"
    )


def traffic_light_widget(active_color: str, timer_value) -> str:
    bulbs_html = "".join(bulb_html(c, c == active_color) for c in ["red", "yellow", "green"])

    housing_html = (
        "<div style='background:#1b1b1b;border-radius:10px;padding:8px 6px;"
        "width:56px;margin:auto;box-shadow:0 3px 8px rgba(0,0,0,0.5);'>"
        f"{bulbs_html}</div>"
    )

    timer_text = f"{timer_value:02d}" if timer_value is not None else "--"
    timer_html = (
        "<div style='background:#000;border:2px solid #222;border-radius:6px;"
        "width:52px;margin:6px auto 0 auto;padding:3px 0;text-align:center;'>"
        f"<span style='color:#ff2b2b;font-family:\"Courier New\",monospace;"
        f"font-weight:bold;font-size:22px;letter-spacing:1px;'>{timer_text}</span></div>"
    )

    return housing_html + timer_html


def road_block(road_name: str, color: str, vehicle_count: int, timer_value):
    st.markdown(traffic_light_widget(color, timer_value), unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center;margin:4px 0 0 0;'><b>{road_name}</b><br>"
        f"{vehicle_count} vehicles</p>",
        unsafe_allow_html=True,
    )


def draw_junction(light_state: Dict[str, str], counts: Dict[str, int], timers: Dict[str, int], status_text: str):
    st.markdown(f"#### {status_text}")

    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        road_block("North", light_state["North"], counts["North"], timers["North"])

    left, mid, right = st.columns([1, 1, 1])
    with left:
        road_block("West", light_state["West"], counts["West"], timers["West"])
    with mid:
        st.markdown(
            "<div style='width:80px;height:80px;background:#34495e;"
            "margin:45px auto;border-radius:50%;display:flex;"
            "align-items:center;justify-content:center;text-align:center;"
            "color:white;font-size:13px;font-weight:bold;'>Junction</div>",
            unsafe_allow_html=True,
        )
    with right:
        road_block("East", light_state["East"], counts["East"], timers["East"])

    _, mid, _ = st.columns([1, 1, 1])
    with mid:
        road_block("South", light_state["South"], counts["South"], timers["South"])


def run_one_cycle(cycle_number: int, counts: Dict[str, int], display_box) -> Dict[str, int]:
    selected_road = choose_road(counts)
    green_time = calculate_green_time(counts[selected_road])

    for seconds_left in range(green_time, 0, -1):
        light_state = {road: ("green" if road == selected_road else "red") for road in ROADS}
        timers = {road: (seconds_left if road == selected_road else None) for road in ROADS}
        with display_box.container():
            draw_junction(
                light_state,
                counts,
                timers,
                f"Cycle {cycle_number}: {selected_road} Road is GREEN ({seconds_left}s left)",
            )
        time.sleep(1)

    for seconds_left in range(YELLOW_TIME, 0, -1):
        light_state = {road: ("yellow" if road == selected_road else "red") for road in ROADS}
        timers = {road: (seconds_left if road == selected_road else None) for road in ROADS}
        with display_box.container():
            draw_junction(
                light_state,
                counts,
                timers,
                f"Cycle {cycle_number}: {selected_road} Road is YELLOW ({seconds_left}s left)",
            )
        time.sleep(1)

    light_state = {road: "red" for road in ROADS}
    timers = {road: None for road in ROADS}
    with display_box.container():
        draw_junction(light_state, counts, timers, f"Cycle {cycle_number}: All roads RED (safety gap)")
    time.sleep(ALL_RED_GAP)

    return {
        "Cycle": cycle_number,
        "Road Made Green": selected_road,
        "Vehicles On That Road": counts[selected_road],
        "Green Time (s)": green_time,
        "North": counts["North"],
        "South": counts["South"],
        "East": counts["East"],
        "West": counts["West"],
    }


def main() -> None:
    st.title("🚦 Smart Traffic Signal System")

    with st.form("vehicle_input_form"):
        col1, col2 = st.columns(2)
        with col1:
            north_input = st.number_input("North Road - vehicles", min_value=0, max_value=100, value=10)
            south_input = st.number_input("South Road - vehicles", min_value=0, max_value=100, value=6)
        with col2:
            east_input = st.number_input("East Road - vehicles", min_value=0, max_value=100, value=18)
            west_input = st.number_input("West Road - vehicles", min_value=0, max_value=100, value=8)

        num_cycles = st.slider("How many signal cycles should run?", min_value=1, max_value=10, value=4)
        submitted = st.form_submit_button("🚦 Start Traffic System")

    if "log" not in st.session_state:
        st.session_state.log = []

    if submitted:
        counts = {
            "North": north_input,
            "South": south_input,
            "East": east_input,
            "West": west_input,
        }

        display_box = st.empty()
        cycle_log = []

        for cycle_number in range(1, num_cycles + 1):
            result = run_one_cycle(cycle_number, counts, display_box)
            cycle_log.append(result)
            counts = new_traffic_reading()

        st.session_state.log = cycle_log
        st.success("✅ Simulation finished! Scroll down to see the full log.")

    if st.session_state.log:
        st.subheader("📋 Traffic Signal Log")
        log_df = pd.DataFrame(st.session_state.log)
        st.dataframe(log_df, width="stretch")

    st.divider()


if __name__ == "__main__":
    main()
