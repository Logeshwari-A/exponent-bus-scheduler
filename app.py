from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from bus_scheduler.formatting import bus_timelines_to_rows, scenario_input_rows, station_rows
from bus_scheduler.loader import load_all_scenarios
from bus_scheduler.scheduler import schedule_scenario


ROOT = Path(__file__).resolve().parent
SCENARIOS_DIR = ROOT / "data" / "scenarios"


st.set_page_config(page_title="Bus Charging Scheduler", layout="wide")


@st.cache_data(show_spinner=False)
def load_data() -> list:
    return load_all_scenarios(SCENARIOS_DIR)


@st.cache_data(show_spinner=False)
def run_schedule(scenario_id: str):
    scenarios = {scenario.scenario_id: scenario for scenario in load_data()}
    return schedule_scenario(scenarios[scenario_id])


def main() -> None:
    st.title("Bus Charging Scheduler")
    scenarios = load_data()
    selected_scenario = st.selectbox("Scenario", scenarios, format_func=lambda scenario: scenario.name)
    st.caption(selected_scenario.description)

    st.subheader("Scenario input")
    st.dataframe(pd.DataFrame(scenario_input_rows(selected_scenario)), use_container_width=True, hide_index=True)

    result = run_schedule(selected_scenario.scenario_id)

    st.subheader("Per-bus timetable")
    st.dataframe(pd.DataFrame(bus_timelines_to_rows(result)), use_container_width=True, hide_index=True)

    st.subheader("Per-station charging order")
    for station in selected_scenario.route.station_names:
        with st.expander(f"Station {station}", expanded=station == selected_scenario.route.station_names[0]):
            st.dataframe(pd.DataFrame(station_rows(result, station)), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
