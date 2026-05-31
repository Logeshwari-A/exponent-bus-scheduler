# exponent-bus-scheduler

Python + Streamlit bus charging scheduler for the Exponent take-home.

## Run locally

```bash
pip install -r requirements.txt
streamlit run app.py
```
 
## Hosted app

The app is hosted on Streamlit Community Cloud:

https://exponent-bus-scheduler.streamlit.app


## What is implemented

- Scenario loading from JSON files in `data/scenarios`
- Deterministic schedule generation
- Per-bus and per-station output views in Streamlit

## How to change a weight

Edit the `weights` block in a scenario JSON file. The scheduler reads the values directly from the scenario.

## How to add a new rule

Add a rule class in `bus_scheduler/rules.py`, register it in `DEFAULT_RULES`, and add the matching weight field to `Weights`.