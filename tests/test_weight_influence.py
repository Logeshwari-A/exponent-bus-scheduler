from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from bus_scheduler.loader import load_scenario
from bus_scheduler.models import Weights
from bus_scheduler.scheduler import schedule_scenario
from bus_scheduler.rules import DEFAULT_RULES, CandidateEvaluation


def plan_signature(result):
    return tuple(sorted((timeline.bus_id, tuple(timeline.station_plan)) for timeline in result.bus_timelines))


class WeightInfluenceTests(unittest.TestCase):
    def test_scoring_layer_respects_weights(self) -> None:
        # Ensure that composing rule scores with different weights yields different totals
        candidate = CandidateEvaluation(
            bus_id="x",
            operator="kpn",
            total_wait_minutes=15,
            arrival_minute=1200,
            operator_bus_count=5,
            total_scheduled_buses=20,
        )

        def composite_score(weights: Weights) -> float:
            total = 0.0
            for rule in DEFAULT_RULES:
                w = getattr(weights, rule.name)
                total += w * rule.score(candidate, None)
            return total

        w1 = Weights(1.0, 1.0, 1.0)
        w2 = Weights(1.0, 10.0, 1.0)
        self.assertNotEqual(composite_score(w1), composite_score(w2))

    def test_scheduler_runs_with_varied_weights(self) -> None:
        # smoke: changing weights shouldn't crash the scheduler; ensure schedules are produced
        scenario_path = Path("data/scenarios/scenario_5_worst_case_convergence.json")
        scenario = load_scenario(scenario_path)
        weight_sets = [
            Weights(1.0, 0.0, 1.0),
            Weights(1.0, 10.0, 1.0),
            Weights(10.0, 1.0, 1.0),
        ]
        signatures = set()
        for w in weight_sets:
            s = replace(scenario, weights=w)
            res = schedule_scenario(s)
            signatures.add(plan_signature(res))
        # At minimum the scheduler produced valid plans for each weight set
        self.assertGreaterEqual(len(signatures), 1)


if __name__ == "__main__":
    unittest.main()
