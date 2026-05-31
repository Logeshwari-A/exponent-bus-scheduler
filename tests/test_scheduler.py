from __future__ import annotations

import unittest
from pathlib import Path

from bus_scheduler.loader import load_all_scenarios
from bus_scheduler.scheduler import schedule_scenario


ROOT = Path(__file__).resolve().parents[1]


class SchedulerSmokeTests(unittest.TestCase):
    def test_all_scenarios_schedule(self) -> None:
        scenarios = load_all_scenarios(ROOT / "data" / "scenarios")
        self.assertEqual(len(scenarios), 5)

        for scenario in scenarios:
            result = schedule_scenario(scenario)
            self.assertEqual(len(result.bus_timelines), len(scenario.buses))

    def test_hard_constraints_hold(self) -> None:
        scenarios = load_all_scenarios(ROOT / "data" / "scenarios")

        for scenario in scenarios:
            result = schedule_scenario(scenario)
            route = scenario.route
            bus_direction = {bus.bus_id: bus.direction for bus in scenario.buses}

            for timeline in result.bus_timelines:
                ordered_nodes = route.ordered_nodes(bus_direction[timeline.bus_id])
                previous_node = ordered_nodes[0]
                for event in timeline.charges:
                    self.assertLessEqual(
                        route.distance_between(previous_node, event.station),
                        route.battery_range_km,
                    )
                    previous_node = event.station
                self.assertLessEqual(
                    route.distance_between(previous_node, ordered_nodes[-1]),
                    route.battery_range_km,
                )

            for events in result.station_events.values():
                for left, right in zip(events, events[1:]):
                    self.assertLessEqual(left.charge_end_minute, right.charge_start_minute)


if __name__ == "__main__":
    unittest.main()
