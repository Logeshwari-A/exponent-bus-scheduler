# Architecture

This first implementation uses a deterministic, event-driven greedy scheduler. Hard feasibility is checked first, then each feasible charging plan is scored with pluggable rules driven by scenario weights.

## Design Goals

- Keep the route, buses, stations, and weights in data.
- Keep hard constraints separate from soft optimization.
- Make new rules additive, not invasive.
- Make weight changes a data change, not a code change.

## Core Data Model

- `RouteDefinition` describes the route as an ordered list of nodes plus segment distances.
- `BusDefinition` captures bus id, operator, direction, and departure time.
- `Weights` holds the three soft objectives in one place.
- `ScenarioDefinition` bundles route, weights, and bus departures.
- `BusTimeline` and `StationChargeEvent` form the scheduling output.

## Scheduler Approach

The scheduler sorts buses by departure time, enumerates all feasible charging plans for each bus, simulates the bus against the current station calendars, and picks the lowest-scoring plan.

Scoring is implemented as separate rules:

- individual wait time
- operator smoothness proxy
- overall network completion time

Each rule returns a numeric score and the scenario weights decide how much it matters.

## Future Changes Anticipated

- Priority buses: add a field to `BusDefinition` and a new rule term.
- Time-based charging costs: add a cost function to the rule layer.
- Driver shifts: add a feasibility rule for time windows.
- More stations: extend the route data, not the scheduler API.
- Multiple chargers per station: replace station availability with capacity-based scheduling data.
- New operators: operators remain data values, not enums embedded in logic.
- Different route distances: update `RouteDefinition` only.
- New soft rules: implement another rule class and register it.
- Scenario-specific overrides: keep them in JSON so the engine remains unchanged.

## Changing a Weight

Update the scenario JSON only:

```json
"weights": {"individual": 1.0, "operator": 2.0, "overall": 1.0}
```

## Adding a New Rule

Add a new rule object in `bus_scheduler/rules.py` and include it in `DEFAULT_RULES`. The scheduler automatically multiplies it by the matching weight field.

## Assumptions

- Speed defaults to 60 km/h.
- Station charging is always 25 minutes and always to full.
- The route is linear with no backtracking.
- Bus scheduling is deterministic and tie-broken by score, number of charges, finish time, then plan order.
