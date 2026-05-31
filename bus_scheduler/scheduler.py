from __future__ import annotations

from dataclasses import dataclass, field

from bus_scheduler.models import (
    BusChargeEvent,
    BusDefinition,
    BusTimeline,
    Direction,
    RouteDefinition,
    ScenarioDefinition,
    ScheduleResult,
    StationChargeEvent,
)
from bus_scheduler.rules import CandidateEvaluation, DEFAULT_RULES


@dataclass
class SchedulerState:
    station_available_at: dict[str, int] = field(default_factory=dict)
    operator_bus_count: dict[str, int] = field(default_factory=dict)
    total_scheduled_buses: int = 0


def parse_time_to_minute(time_value: str) -> int:
    hour_text, minute_text = time_value.split(":")
    return int(hour_text) * 60 + int(minute_text)


def format_minute(minute_value: int) -> str:
    hour = (minute_value // 60) % 24
    minute = minute_value % 60
    return f"{hour:02d}:{minute:02d}"


def _partial_plan_feasible(route: RouteDefinition, ordered_nodes: list[str], plan: list[str]) -> bool:
    battery_range = route.battery_range_km
    current = ordered_nodes[0]
    for station in plan:
        if route.distance_between(current, station) > battery_range:
            return False
        current = station
    return True


def _complete_plan_feasible(route: RouteDefinition, ordered_nodes: list[str], plan: list[str]) -> bool:
    if not _partial_plan_feasible(route, ordered_nodes, plan):
        return False
    current = ordered_nodes[0] if not plan else plan[-1]
    return route.distance_between(current, ordered_nodes[-1]) <= route.battery_range_km


def enumerate_feasible_plans(route: RouteDefinition, direction: Direction) -> list[list[str]]:
    ordered_nodes = route.ordered_nodes(direction)
    stations = ordered_nodes[1:-1]
    plans: list[list[str]] = []

    def search(start_index: int, current_plan: list[str]) -> None:
        if _complete_plan_feasible(route, ordered_nodes, current_plan):
            plans.append(list(current_plan))
        for index in range(start_index, len(stations)):
            next_station = stations[index]
            trial_plan = current_plan + [next_station]
            if _partial_plan_feasible(route, ordered_nodes, trial_plan):
                search(index + 1, trial_plan)

    search(0, [])
    plans.sort(key=lambda plan: (len(plan), plan))
    return plans


def _simulate_plan(
    bus: BusDefinition,
    route: RouteDefinition,
    plan: list[str],
    station_available_at: dict[str, int],
) -> tuple[BusTimeline, list[StationChargeEvent]]:
    ordered_nodes = route.ordered_nodes(bus.direction)
    current_node = ordered_nodes[0]
    current_time = parse_time_to_minute(bus.departure_time)
    charges: list[BusChargeEvent] = []
    station_events: list[StationChargeEvent] = []
    total_wait = 0

    for station in plan:
        travel_distance = route.distance_between(current_node, station)
        current_time += int(route.travel_minutes(travel_distance))
        arrival = current_time
        station_free_at = station_available_at.get(station, 0)
        charge_start = max(arrival, station_free_at)
        wait_minutes = charge_start - arrival
        charge_end = charge_start + route.charge_minutes
        total_wait += wait_minutes
        station_available_at[station] = charge_end
        charges.append(
            BusChargeEvent(
                station=station,
                arrival_minute=arrival,
                charge_start_minute=charge_start,
                charge_end_minute=charge_end,
                wait_minutes=wait_minutes,
            )
        )
        station_events.append(
            StationChargeEvent(
                station=station,
                bus_id=bus.bus_id,
                operator=bus.operator,
                direction=bus.direction,
                arrival_minute=arrival,
                charge_start_minute=charge_start,
                charge_end_minute=charge_end,
                wait_minutes=wait_minutes,
            )
        )
        current_time = charge_end
        current_node = station

    final_travel_distance = route.distance_between(current_node, ordered_nodes[-1])
    arrival_minute = current_time + int(route.travel_minutes(final_travel_distance))
    timeline = BusTimeline(
        bus_id=bus.bus_id,
        operator=bus.operator,
        direction=bus.direction,
        departure_minute=parse_time_to_minute(bus.departure_time),
        charges=charges,
        arrival_minute=arrival_minute,
        total_wait_minutes=total_wait,
        station_plan=list(plan),
    )
    return timeline, station_events


def _evaluate_candidate(
    bus: BusDefinition,
    route: RouteDefinition,
    plan: list[str],
    state: SchedulerState,
    scenario: ScenarioDefinition,
) -> tuple[BusTimeline, list[StationChargeEvent], float]:
    station_available_at = dict(state.station_available_at)
    timeline, station_events = _simulate_plan(bus, route, plan, station_available_at)
    candidate = CandidateEvaluation(
        bus_id=bus.bus_id,
        operator=bus.operator,
        total_wait_minutes=timeline.total_wait_minutes,
        arrival_minute=timeline.arrival_minute,
        operator_bus_count=state.operator_bus_count.get(bus.operator, 0),
        total_scheduled_buses=state.total_scheduled_buses,
    )
    score = 0.0
    for rule in DEFAULT_RULES:
        weight = getattr(scenario.weights, rule.name)
        score += weight * rule.score(candidate, scenario)
    return timeline, station_events, score


def schedule_scenario(scenario: ScenarioDefinition) -> ScheduleResult:
    state = SchedulerState(
        station_available_at={station: 0 for station in scenario.route.station_names},
        operator_bus_count={},
        total_scheduled_buses=0,
    )
    bus_timelines: list[BusTimeline] = []
    station_events: dict[str, list[StationChargeEvent]] = {station: [] for station in scenario.route.station_names}

    ordered_buses = sorted(
        scenario.buses,
        key=lambda bus: (parse_time_to_minute(bus.departure_time), bus.bus_id),
    )

    for bus in ordered_buses:
        plans = enumerate_feasible_plans(scenario.route, bus.direction)
        best_timeline: BusTimeline | None = None
        best_station_events: list[StationChargeEvent] = []
        best_score = float("inf")

        for plan in plans:
            timeline, candidate_station_events, score = _evaluate_candidate(bus, scenario.route, plan, state, scenario)
            tie_break = (score, len(plan), timeline.arrival_minute, plan)
            best_tie_break = (
                best_score,
                len(best_timeline.station_plan) if best_timeline else 10**9,
                best_timeline.arrival_minute if best_timeline else 10**9,
                best_timeline.station_plan if best_timeline else [],
            )
            if tie_break < best_tie_break:
                best_timeline = timeline
                best_station_events = candidate_station_events
                best_score = score

        if best_timeline is None:
            raise ValueError(f"No feasible charging plan found for {bus.bus_id}")

        best_timeline = BusTimeline(
            bus_id=best_timeline.bus_id,
            operator=best_timeline.operator,
            direction=best_timeline.direction,
            departure_minute=best_timeline.departure_minute,
            charges=best_timeline.charges,
            arrival_minute=best_timeline.arrival_minute,
            total_wait_minutes=best_timeline.total_wait_minutes,
            station_plan=best_timeline.station_plan,
            score=best_score,
        )
        bus_timelines.append(best_timeline)
        for event in best_station_events:
            station_events[event.station].append(event)

        for event in best_station_events:
            state.station_available_at[event.station] = event.charge_end_minute
        state.operator_bus_count[bus.operator] = state.operator_bus_count.get(bus.operator, 0) + 1
        state.total_scheduled_buses += 1

    for events in station_events.values():
        events.sort(key=lambda event: (event.charge_start_minute, event.bus_id))

    return ScheduleResult(
        scenario_id=scenario.scenario_id,
        scenario_name=scenario.name,
        bus_timelines=bus_timelines,
        station_events=station_events,
    )
