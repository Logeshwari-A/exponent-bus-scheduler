from __future__ import annotations

import unittest
from pathlib import Path

from dataclasses import replace

from bus_scheduler.loader import load_scenario
from bus_scheduler.models import ScenarioDefinition, BusDefinition
from bus_scheduler.scheduler import schedule_scenario


class CapacityTieTests(unittest.TestCase):
    def test_equal_arrival_tie_does_not_overlap(self) -> None:
        """Create two buses with identical departure times and ensure no station overlaps.

        This targets the edge case where multiple buses arrive at the same minute
        and station capacity is 1; scheduling must still produce non-overlapping
        charge intervals.
        """
        template = load_scenario(Path(__file__).resolve().parents[1] / "data" / "scenarios" / "scenario_1_even_spacing.json")
        # pick a base bus and create a duplicate with a new id but same departure
        base_bus = template.buses[0]
        dup_bus = BusDefinition(
            bus_id=f"{base_bus.bus_id}-DUP",
            operator=base_bus.operator,
            direction=base_bus.direction,
            departure_time=base_bus.departure_time,
        )

        small_scenario = ScenarioDefinition(
            scenario_id="tie-test",
            name="Tie Test",
            description="two buses same departure",
            route=template.route,
            weights=template.weights,
            buses=[base_bus, dup_bus],
        )

        result = schedule_scenario(small_scenario)

        for events in result.station_events.values():
            for left, right in zip(events, events[1:]):
                self.assertLessEqual(left.charge_end_minute, right.charge_start_minute)


if __name__ == "__main__":
    unittest.main()
