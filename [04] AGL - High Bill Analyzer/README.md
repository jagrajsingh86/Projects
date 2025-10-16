# POC9 — High Bill Inquiry AI Agent (Local Demo)

This demo uses **synthetic data** to simulate a customer's high-bill inquiry and generates a plain-English explanation with likely drivers.

## Quickstart (VS Code)

```bash
cd app
python -m venv .venv
# Activate venv:
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate

pip install -r requirements.txt
uvicorn api:app --reload
# In a second terminal
pip install streamlit==1.37.0 requests==2.32.3
streamlit run app.py
```

Then open the Streamlit URL and try Customer IDs **1001–1010**.

## What it does

- Loads bills and 30-min interval data for previous vs current periods.
- Computes change in total kWh and basic drivers (heating/cooling correlation to temperature, evening peak share).
- Returns a **natural-language message** suitable for a ServiceNow Virtual Agent or Agent Workspace panel.
- Uses a tiny FastAPI backend (as a stand-in for ServiceNow action orchestration).
- Front-end is Streamlit for speed (swap with VA later).

## Files
- `data/` — synthetic CSVs
- `app/analyzer.py` — core logic
- `app/api.py` — FastAPI endpoint `/explain`
- `app/app.py` — Streamlit demo UI
- `app/requirements.txt`

## Next steps (to productionize)
1. Replace synthetic CSVs with **billing/AMI API connectors** or secure extracts.
2. Add **HDD/CDD** from weather APIs and tariff catalog for cost decomposition.
3. Implement **guardrails** and human-in-the-loop for sensitive advice.
4. Integrate with **ServiceNow VA** and **Agent Workspace** (RAG over KB).



## Virtual Agent (Mock)
- Inspect `va_mock/intents.json` for a lightweight intent definition.
- The Streamlit app shows a **response-card** JSON payload that a VA could render.

## Charts
The UI now renders:
1. Previous period **daily kWh** (matplotlib)
2. Current period **daily kWh** (matplotlib)
3. Current period **Temperature vs 30-min kWh** scatter (matplotlib)
