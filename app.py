from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

from dataclasses import replace

from bus_scheduler.formatting import (
    bus_timelines_to_rows,
    scenario_input_rows,
    station_rows,
    bus_charge_rows,
)
from bus_scheduler.loader import load_all_scenarios
from bus_scheduler.models import Weights
from bus_scheduler.scheduler import schedule_scenario, format_minute


ROOT = Path(__file__).resolve().parent
SCENARIOS_DIR = ROOT / "data" / "scenarios"


st.set_page_config(page_title="Bus Charging Scheduler", layout="wide")


@st.cache_data(show_spinner=False)
def load_data() -> list:
    """Load all scenario definitions from the `data/scenarios` folder.

    Returns a list of `ScenarioDefinition` objects used by the UI.
    """
    return load_all_scenarios(SCENARIOS_DIR)


@st.cache_data(show_spinner=False)
def run_schedule(scenario_id: str):
    """Run the scheduler for the selected scenario id.

    The UI passes an overridden `Weights` object (from the sidebar) by
    creating a replaced scenario instance before calling the scheduler.
    """
    scenarios = {scenario.scenario_id: scenario for scenario in load_data()}
    return schedule_scenario(scenarios[scenario_id])


def main() -> None:
    st.title("Bus Charging Scheduler")
    scenarios = load_data()
    selected_scenario = st.selectbox("Scenario", scenarios, format_func=lambda scenario: scenario.name)
    st.caption(selected_scenario.description)

    st.sidebar.header("Weights")
    w_ind = st.sidebar.number_input("Individual weight", value=selected_scenario.weights.individual, min_value=0.0, step=0.1)
    w_op = st.sidebar.number_input("Operator weight", value=selected_scenario.weights.operator, min_value=0.0, step=0.1)
    w_over = st.sidebar.number_input("Overall weight", value=selected_scenario.weights.overall, min_value=0.0, step=0.1)

    override_weights = Weights(individual=float(w_ind), operator=float(w_op), overall=float(w_over))
    scenario_to_run = replace(selected_scenario, weights=override_weights)

    st.subheader("Scenario input")
    st.dataframe(pd.DataFrame(scenario_input_rows(selected_scenario)), use_container_width=True, hide_index=True)

    result = schedule_scenario(scenario_to_run)

    st.subheader("Per-bus timetable")
    bus_rows = pd.DataFrame(bus_timelines_to_rows(result))
    st.dataframe(bus_rows, use_container_width=True, hide_index=True)
    csv_buses = bus_rows.to_csv(index=False).encode("utf-8")
    st.download_button("Download per-bus CSV", csv_buses, file_name=f"{selected_scenario.scenario_id}_buses.csv", mime="text/csv")

    st.markdown("---")
    st.markdown("**Per-bus details**")
    for timeline in result.bus_timelines:
        with st.expander(f"{timeline.bus_id} — {timeline.operator} — arrival {format_minute(timeline.arrival_minute)}"):
            df = pd.DataFrame(bus_charge_rows(timeline))
            st.table(df)
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(f"Download {timeline.bus_id} CSV", csv, file_name=f"{timeline.bus_id}_timeline.csv", mime="text/csv")

    st.subheader("Per-station charging order")
    for station in selected_scenario.route.station_names:
        with st.expander(f"Station {station}", expanded=station == selected_scenario.route.station_names[0]):
            df_s = pd.DataFrame(station_rows(result, station))
            st.dataframe(df_s, use_container_width=True, hide_index=True)
            csv_s = df_s.to_csv(index=False).encode("utf-8")
            st.download_button(f"Download {station} CSV", csv_s, file_name=f"{selected_scenario.scenario_id}_{station}_station.csv", mime="text/csv")


if __name__ == "__main__":
    main()
