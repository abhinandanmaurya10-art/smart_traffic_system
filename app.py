"""Streamlit app entrypoint for Adaptive Smart Traffic Signal System."""
from typing import Dict, Optional, Tuple
import time
import pandas as pd
import streamlit as st

from config import ROADS, YELLOW_TIME, ALL_RED_GAP, WEIGHTS, MAX_PEDESTRIAN_WAIT_CYCLES
from logic import RoadState, calculate_green_time, choose_road, update_starvation_counters, new_traffic_reading, fixed_time_choice
from ui_components import draw_junction
import random

st.set_page_config(page_title="Adaptive Smart Traffic Signal System", page_icon="🚦", layout="centered")


def run_one_cycle_adaptive(cycle_number: int, states: Dict[str, RoadState], display_box, weights: Dict[str, float], max_wait_cycles: int) -> Dict[str, int]:
    """Run a single adaptive scheduling cycle and return metrics for logging."""
    selected = choose_road(states, weights, max_wait_cycles)
    if selected is None:
        selected = list(states.keys())[0]
    green_time = calculate_green_time(states[selected].vehicle_count)

    # run green
    for seconds_left in range(green_time, 0, -1):
        light_state = {r: ("green" if r == selected else "red") for r in ROADS}
        timers = {r: (seconds_left if r == selected else None) for r in ROADS}
        with display_box.container():
            draw_junction(light_state, {r: states[r].vehicle_count for r in ROADS}, timers,
                          f"Cycle {cycle_number}: {selected} Road is GREEN ({seconds_left}s left)")
        time.sleep(1)

    # yellow
    for seconds_left in range(YELLOW_TIME, 0, -1):
        light_state = {r: ("yellow" if r == selected else "red") for r in ROADS}
        timers = {r: (seconds_left if r == selected else None) for r in ROADS}
        with display_box.container():
            draw_junction(light_state, {r: states[r].vehicle_count for r in ROADS}, timers,
                          f"Cycle {cycle_number}: {selected} Road is YELLOW ({seconds_left}s left)")
        time.sleep(1)

    # all red gap
    light_state = {r: "red" for r in ROADS}
    timers = {r: None for r in ROADS}
    with display_box.container():
        draw_junction(light_state, {r: states[r].vehicle_count for r in ROADS}, timers,
                      f"Cycle {cycle_number}: All roads RED (safety gap)")
    time.sleep(ALL_RED_GAP)

    # prepare metrics
    metrics = {
        "Cycle": cycle_number,
        "Road Made Green": selected,
        "Vehicles On That Road": states[selected].vehicle_count,
        "Green Time (s)": green_time,
    }

    update_starvation_counters(states, selected)
    return metrics


def run_one_cycle_fixed(cycle_number: int, states: Dict[str, RoadState], display_box, last_index: int) -> Tuple[Dict[str, int], int]:
    chosen = fixed_time_choice(states, last_index)
    green_time = calculate_green_time(states[chosen].vehicle_count)

    for seconds_left in range(green_time, 0, -1):
        light_state = {r: ("green" if r == chosen else "red") for r in ROADS}
        timers = {r: (seconds_left if r == chosen else None) for r in ROADS}
        with display_box.container():
            draw_junction(light_state, {r: states[r].vehicle_count for r in ROADS}, timers,
                          f"[Fixed] Cycle {cycle_number}: {chosen} Road is GREEN ({seconds_left}s left)")
        time.sleep(1)

    for seconds_left in range(YELLOW_TIME, 0, -1):
        light_state = {r: ("yellow" if r == chosen else "red") for r in ROADS}
        timers = {r: (seconds_left if r == chosen else None) for r in ROADS}
        with display_box.container():
            draw_junction(light_state, {r: states[r].vehicle_count for r in ROADS}, timers,
                          f"[Fixed] Cycle {cycle_number}: {chosen} Road is YELLOW ({seconds_left}s left)")
        time.sleep(1)

    light_state = {r: "red" for r in ROADS}
    timers = {r: None for r in ROADS}
    with display_box.container():
        draw_junction(light_state, {r: states[r].vehicle_count for r in ROADS}, timers,
                      f"[Fixed] Cycle {cycle_number}: All roads RED (safety gap)")
    time.sleep(ALL_RED_GAP)

    metrics = {
        "Cycle": cycle_number,
        "Road Made Green": chosen,
        "Vehicles On That Road": states[chosen].vehicle_count,
        "Green Time (s)": green_time,
    }

    update_starvation_counters(states, chosen)
    next_index = (last_index + 1) % len(ROADS)
    return metrics, next_index


def main() -> None:
    st.title("🚦 Adaptive Smart Traffic Signal System")

    # Sidebar settings
    st.sidebar.header("Simulation Settings")
    fixed_time_mode = st.sidebar.checkbox("Enable Fixed-Time Mode (baseline)", value=False)

    st.sidebar.markdown("**Priority Scoring Weights**")
    w1 = st.sidebar.number_input("Vehicle count weight (w1)", value=WEIGHTS["vehicle_count"], step=0.1)
    w2 = st.sidebar.number_input("Waiting time weight (w2)", value=WEIGHTS["waiting_time"], step=0.1)
    w3 = st.sidebar.number_input("Pedestrian weight (w3)", value=WEIGHTS["pedestrian"], step=0.1)
    weights = {"vehicle_count": w1, "waiting_time": w2, "pedestrian": w3}

    st.sidebar.markdown("**Advanced**")
    max_wait_cycles = st.sidebar.number_input("Max wait cycles (starvation)", value=3, min_value=1)

    st.sidebar.markdown("**Manual Requests / Overrides**")
    emergency_flags = {}
    pedestrian_requests = {}
    for r in ROADS:
        emergency_flags[r] = st.sidebar.checkbox(f"Emergency on {r}", value=False, key=f"em_{r}")
        pedestrian_requests[r] = st.sidebar.button(f"Request Walk: {r}", key=f"ped_{r}")

    # Input form
    comparison_mode = st.sidebar.checkbox("Run Fixed vs Adaptive comparison (deterministic)", value=False)
    seed = st.sidebar.number_input("Random seed (for comparison)", value=42)

    with st.form("vehicle_input_form"):
        col1, col2 = st.columns(2)
        with col1:
            north_input = st.number_input("North Road - vehicles", min_value=0, max_value=100, value=10)
            south_input = st.number_input("South Road - vehicles", min_value=0, max_value=100, value=6)
        with col2:
            east_input = st.number_input("East Road - vehicles", min_value=0, max_value=100, value=18)
            west_input = st.number_input("West Road - vehicles", min_value=0, max_value=100, value=8)

        num_cycles = st.slider("How many signal cycles should run?", min_value=1, max_value=20, value=4)
        submitted = st.form_submit_button("🚦 Start Simulation")

    if "log" not in st.session_state:
        st.session_state.log = []

    if submitted:
        # Initialize states
        states = {}
        for r, v in zip(["North", "South", "East", "West"], [north_input, south_input, east_input, west_input]):
            states[r] = RoadState(vehicle_count=v, pedestrian_request=bool(pedestrian_requests.get(r, False)), emergency=bool(emergency_flags.get(r, False)))

        display_box = st.empty()
        cycle_log = []

        throughput_series = []

        # Run simulation (visual, with sleeps)
        fixed_last_index = -1
        from logic import WEIGHTS as logic_WEIGHTS
        logic_WEIGHTS.update(weights)
        for cycle_number in range(1, num_cycles + 1):
            if fixed_time_mode:
                metrics, fixed_last_index = run_one_cycle_fixed(cycle_number, states, display_box, fixed_last_index)
            else:
                metrics = run_one_cycle_adaptive(cycle_number, states, display_box, weights, max_wait_cycles)

            cycle_log.append(metrics)
            throughput_series.append(metrics["Vehicles On That Road"])

            # new traffic for next cycle
            new_readings = new_traffic_reading()
            for r in new_readings:
                states[r].vehicle_count = new_readings[r]

        # If comparison mode selected run deterministic headless comparison
        if comparison_mode:
            sim_readings = []
            rng = random.Random(seed)
            for _ in range(num_cycles):
                sim_readings.append({r: rng.randint(0, 40) for r in ROADS})

            def simulate_headless(mode: str):
                # copy initial states
                sim_states = {r: RoadState(vehicle_count=0) for r in ROADS}
                # start with the initial user-provided readings
                for r in ROADS:
                    sim_states[r].vehicle_count = {"North": north_input, "South": south_input, "East": east_input, "West": west_input}[r]

                log = []
                fixed_idx = -1
                from logic import WEIGHTS as logic_WEIGHTS2
                logic_WEIGHTS2.update(weights)
                for i in range(num_cycles):
                    if mode == "fixed":
                        m, fixed_idx = run_one_cycle_fixed(i + 1, sim_states, st.empty(), fixed_idx)
                    else:
                        m = run_one_cycle_adaptive(i + 1, sim_states, st.empty(), weights, max_wait_cycles)
                    log.append(m)
                    # apply deterministic next readings
                    for r in ROADS:
                        sim_states[r].vehicle_count = sim_readings[i][r]
                return pd.DataFrame(log)

            df_fixed = simulate_headless("fixed")
            df_adapt = simulate_headless("adaptive")

            st.subheader("Comparison: Fixed-Time vs Adaptive")
            comp_df = pd.DataFrame({
                "Metric": ["Average vehicles cleared per cycle", "Total vehicles cleared"],
                "Fixed": [df_fixed["Vehicles On That Road"].mean(), df_fixed["Vehicles On That Road"].sum()],
                "Adaptive": [df_adapt["Vehicles On That Road"].mean(), df_adapt["Vehicles On That Road"].sum()],
            })
            st.table(comp_df)

            st.subheader("Throughput Over Cycles (Adaptive)")
            st.line_chart(df_adapt["Vehicles On That Road"])

        st.session_state.log = cycle_log
        st.success("✅ Simulation finished! Scroll down to see the full log.")

    # log and export
    if st.session_state.log:
        st.subheader("📋 Traffic Signal Log")
        log_df = pd.DataFrame(st.session_state.log)
        st.dataframe(log_df, width="stretch")
        if st.button("Export Log to CSV"):
            csv = log_df.to_csv(index=False)
            st.download_button("Download CSV", csv, file_name="traffic_log.csv", mime="text/csv")

        # show throughput chart for visual run
        if throughput_series:
            st.subheader("Throughput (vehicles cleared per cycle)")
            st.line_chart(pd.Series(throughput_series))


if __name__ == "__main__":
    main()
