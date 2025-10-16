# POC9 — High Bill Inquiry AI Agent (Demo, v3)

This version adds **cause detectors** (EV charging, pool pump, weather-driven heating/cooling, daytime occupancy, solar offline) and surfaces them in the UI + VA response card.

## Run backend
```bash
cd app
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn api:app --reload
```

## Run UI
```bash
# (same venv is fine)
streamlit run app.py
```

## Test
Use Customer IDs 1001–1010. Update the API endpoint in the UI if your port is not 8000.

## Notes
- Data is synthetic. Replace CSVs in `data/` with secure extracts or API connectors.
- Detectors use simple, explainable heuristics suitable for an MVP.
