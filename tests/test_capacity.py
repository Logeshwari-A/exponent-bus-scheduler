from __future__ import annotations

import unittest
from dataclasses import replace
from pathlib import Path

from bus_scheduler.loader import load_scenario
from bus_scheduler.scheduler import schedule_scenario


class CapacityTests(unittest.TestCase):
    def test_increasing_capacity_reduces_total_wait(self) -> None:
        scenario_path = Path("data/scenarios/scenario_5_worst_case_convergence.json")
        scenario = load_scenario(scenario_path)

        # baseline (all stations capacity=1)
        res1 = schedule_scenario(scenario)
        total_wait_1 = sum(t.total_wait_minutes for t in res1.bus_timelines)

        # increase capacity to 2 for all stations
        caps = {s: 2 for s in scenario.route.station_names}
        new_route = replace(scenario.route, station_capacities=caps)
        scenario2 = replace(scenario, route=new_route)
        res2 = schedule_scenario(scenario2)
        total_wait_2 = sum(t.total_wait_minutes for t in res2.bus_timelines)

        self.assertLessEqual(total_wait_2, total_wait_1)


if __name__ == "__main__":
    unittest.main()
