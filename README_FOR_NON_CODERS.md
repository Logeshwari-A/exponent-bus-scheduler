README for Non-Coders
=====================

This brief document explains the project at a high level for reviewers
who are not developers.

What this project does
- Simulates charging schedules for electric buses on a single route.
- Decides where each bus should charge, and in what order buses use each
  charger when there is contention.

How to use the app (non-technical)
1. Open the hosted app: https://exponent-bus-scheduler.streamlit.app
2. Choose a scenario from the top dropdown.
3. (Optional) Use the sidebar numbers to change the three weights:
   - Individual: reduce how much any one bus should wait.
   - Operator: keep buses from the same company more evenly spread.
   - Overall: reduce total time across all buses.
4. Read the scenario input table and look at per-bus timelines.
5. Open a station to see the order of buses that charged there.

Which files contain what (short)
- `app.py`: the small web UI (what reviewers will use).
- `data/scenarios/*.json`: the five scenario inputs.
- `bus_scheduler/scheduler.py`: the scheduling engine (core logic).
- `bus_scheduler/rules.py`: scoring rules used to pick plans.
- `bus_scheduler/loader.py`: reads the scenario files.
- `README.md`, `ARCHITECTURE.md`: developer-facing docs.
- `README_FOR_NON_CODERS.md`: this file (high-level, no code).

If you'd like a guided demo script or a video walkthrough inserted
into the README, I can add that next.
