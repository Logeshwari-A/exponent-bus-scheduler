from __future__ import annotations

import json
from pathlib import Path

from bus_scheduler.models import BusDefinition, RouteDefinition, ScenarioDefinition, Weights


def _parse_route(route_data: dict) -> RouteDefinition:
    return RouteDefinition(
        name=route_data["name"],
        nodes=list(route_data["nodes"]),
        segment_distances_km=list(route_data["segment_distances_km"]),
        speed_kmph=float(route_data.get("speed_kmph", 60.0)),
        battery_range_km=float(route_data.get("battery_range_km", 240.0)),
        charge_minutes=int(route_data.get("charge_minutes", 25)),
        station_capacities=dict(route_data.get("station_capacities", {})),
    )


def _parse_weights(weights_data: dict | None) -> Weights:
    weights_data = weights_data or {}
    return Weights(
        individual=float(weights_data.get("individual", 1.0)),
        operator=float(weights_data.get("operator", 1.0)),
        overall=float(weights_data.get("overall", 1.0)),
    )


def load_scenario(path: Path) -> ScenarioDefinition:
    data = json.loads(path.read_text(encoding="utf-8"))
    route = _parse_route(data["route"])
    weights = _parse_weights(data.get("weights"))
    buses = [
        BusDefinition(
            bus_id=bus["bus_id"],
            operator=bus["operator"],
            direction=bus["direction"],
            departure_time=bus["departure_time"],
        )
        for bus in data["buses"]
    ]
    return ScenarioDefinition(
        scenario_id=data["scenario_id"],
        name=data["name"],
        description=data.get("description", ""),
        route=route,
        weights=weights,
        buses=buses,
    )


def load_all_scenarios(directory: Path) -> list[ScenarioDefinition]:
    return [load_scenario(path) for path in sorted(directory.glob("*.json"))]
