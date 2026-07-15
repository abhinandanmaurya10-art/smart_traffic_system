"""Streamlit UI components for the Adaptive Smart Traffic Signal System."""
from typing import Dict, Optional

import streamlit as st

from config import BULB_ON, BULB_OFF, LIGHT_COLORS


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


def traffic_light_widget(active_color: str, timer_value: Optional[int]) -> str:
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


def road_block(road_name: str, color: str, vehicle_count: int, timer_value: Optional[int]):
    st.markdown(traffic_light_widget(color, timer_value), unsafe_allow_html=True)
    st.markdown(
        f"<p style='text-align:center;margin:4px 0 0 0;'><b>{road_name}</b><br>"
        f"{vehicle_count} vehicles</p>",
        unsafe_allow_html=True,
    )


def draw_junction(light_state: Dict[str, str], counts: Dict[str, int], timers: Dict[str, Optional[int]], status_text: str):
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
