from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


Direction = Literal["bengaluru_to_kochi", "kochi_to_bengaluru"]


@dataclass(frozen=True)
class RouteDefinition:
    name: str
    nodes: list[str]
    segment_distances_km: list[float]
    speed_kmph: float = 60.0
    battery_range_km: float = 240.0
    charge_minutes: int = 25
    station_capacities: dict[str, int] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if len(self.nodes) < 2:
            raise ValueError("route must contain at least a start and end node")
        if len(self.segment_distances_km) != len(self.nodes) - 1:
            raise ValueError("segment_distances_km must be one shorter than nodes")

    @property
    def station_names(self) -> list[str]:
        return self.nodes[1:-1]

    def station_capacity_map(self) -> dict[str, int]:
        stations = self.station_names
        return {s: int(self.station_capacities.get(s, 1)) for s in stations}

    @property
    def total_distance_km(self) -> float:
        return float(sum(self.segment_distances_km))

    @property
    def node_positions_km(self) -> dict[str, float]:
        positions: dict[str, float] = {self.nodes[0]: 0.0}
        distance = 0.0
        for index, segment_distance in enumerate(self.segment_distances_km, start=1):
            distance += segment_distance
            positions[self.nodes[index]] = distance
        return positions

    def ordered_nodes(self, direction: Direction) -> list[str]:
        if direction == "bengaluru_to_kochi":
            return list(self.nodes)
        return list(reversed(self.nodes))

    def travel_minutes(self, distance_km: float) -> float:
        return (distance_km / self.speed_kmph) * 60.0

    def distance_between(self, origin: str, destination: str) -> float:
        positions = self.node_positions_km
        return abs(positions[destination] - positions[origin])


@dataclass(frozen=True)
class BusDefinition:
    bus_id: str
    operator: str
    direction: Direction
    departure_time: str


@dataclass(frozen=True)
class Weights:
    individual: float = 1.0
    operator: float = 1.0
    overall: float = 1.0


@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    name: str
    description: str
    route: RouteDefinition
    weights: Weights
    buses: list[BusDefinition]


@dataclass(frozen=True)
class BusChargeEvent:
    station: str
    arrival_minute: int
    charge_start_minute: int
    charge_end_minute: int
    wait_minutes: int


@dataclass(frozen=True)
class BusTimeline:
    bus_id: str
    operator: str
    direction: Direction
    departure_minute: int
    charges: list[BusChargeEvent] = field(default_factory=list)
    arrival_minute: int = 0
    total_wait_minutes: int = 0
    station_plan: list[str] = field(default_factory=list)
    score: float = 0.0


@dataclass(frozen=True)
class StationChargeEvent:
    station: str
    bus_id: str
    operator: str
    direction: Direction
    arrival_minute: int
    charge_start_minute: int
    charge_end_minute: int
    wait_minutes: int


@dataclass(frozen=True)
class ScheduleResult:
    scenario_id: str
    scenario_name: str
    bus_timelines: list[BusTimeline]
    station_events: dict[str, list[StationChargeEvent]]
