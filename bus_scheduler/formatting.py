from __future__ import annotations

from bus_scheduler.models import ScheduleResult
from bus_scheduler.scheduler import format_minute


def bus_timelines_to_rows(result: ScheduleResult) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for timeline in result.bus_timelines:
        rows.append(
            {
                "bus_id": timeline.bus_id,
                "operator": timeline.operator,
                "direction": timeline.direction,
                "departure": format_minute(timeline.departure_minute),
                "charging_plan": " -> ".join(timeline.station_plan) if timeline.station_plan else "Direct",
                "wait_minutes": timeline.total_wait_minutes,
                "arrival": format_minute(timeline.arrival_minute),
                "score": round(timeline.score, 2),
            }
        )
    return rows


def station_rows(result: ScheduleResult, station: str) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for event in result.station_events.get(station, []):
        rows.append(
            {
                "bus_id": event.bus_id,
                "operator": event.operator,
                "direction": event.direction,
                "arrival": format_minute(event.arrival_minute),
                "start": format_minute(event.charge_start_minute),
                "end": format_minute(event.charge_end_minute),
                "wait_minutes": event.wait_minutes,
            }
        )
    return rows


def scenario_input_rows(scenario) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for bus in scenario.buses:
        rows.append(
            {
                "bus_id": bus.bus_id,
                "operator": bus.operator,
                "direction": bus.direction,
                "departure": bus.departure_time,
            }
        )
    return rows


def bus_charge_rows(timeline) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for idx, charge in enumerate(timeline.charges, start=1):
        rows.append(
            {
                "stop": idx,
                "station": charge.station,
                "arrival": format_minute(charge.arrival_minute),
                "start": format_minute(charge.charge_start_minute),
                "end": format_minute(charge.charge_end_minute),
                "wait_minutes": charge.wait_minutes,
            }
        )
    return rows
