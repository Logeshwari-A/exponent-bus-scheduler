from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from bus_scheduler.models import ScenarioDefinition


@dataclass(frozen=True)
class CandidateEvaluation:
    bus_id: str
    operator: str
    total_wait_minutes: int
    arrival_minute: int
    operator_bus_count: int
    total_scheduled_buses: int


class SchedulingRule(Protocol):
    name: str

    def score(self, candidate: CandidateEvaluation, scenario: ScenarioDefinition) -> float:
        ...


@dataclass(frozen=True)
class IndividualWaitRule:
    name: str = "individual"

    def score(self, candidate: CandidateEvaluation, scenario: ScenarioDefinition) -> float:
        return float(candidate.total_wait_minutes)


@dataclass(frozen=True)
class OperatorSmoothnessRule:
    name: str = "operator"

    def score(self, candidate: CandidateEvaluation, scenario: ScenarioDefinition) -> float:
        density = candidate.operator_bus_count / max(1, candidate.total_scheduled_buses)
        return float(candidate.total_wait_minutes) * (1.0 + density)


@dataclass(frozen=True)
class OverallNetworkRule:
    name: str = "overall"

    def score(self, candidate: CandidateEvaluation, scenario: ScenarioDefinition) -> float:
        return float(candidate.arrival_minute)


DEFAULT_RULES: list[SchedulingRule] = [
    IndividualWaitRule(),
    OperatorSmoothnessRule(),
    OverallNetworkRule(),
]
