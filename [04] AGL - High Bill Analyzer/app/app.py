import streamlit as st
import pandas as pd
import requests
import json
import matplotlib.pyplot as plt

st.set_page_config(page_title="High Bill Inquiry (POC9)", layout="wide")
st.title("High Bill Inquiry — AI-powered Explanation (POC9)")

st.markdown("Enter a **Customer ID** from the synthetic dataset (1001–1010):")
cid = st.number_input("Customer ID", min_value=1001, max_value=1010, value=1005, step=1)

with st.sidebar:
    st.header("Virtual Agent (Mock)")
    st.write("Simulate a ServiceNow VA intent → HTTP action.")
    user_utterance = st.text_input("User says", value="Why is my bill so high?")
    st.caption("This drives the 'high_bill_inquiry' intent and calls the API with the selected Customer ID.")

col1, col2 = st.columns(2)
with col1:
    st.subheader("Step 1 — Fetch & Compare Bills")
with col2:
    st.subheader("Step 2 — Generate Explanation")

st.info("Run the API locally first: `uvicorn api:app --reload` (in the `app` folder).")
endpoint = st.text_input("API endpoint", value="http://127.0.0.1:8000/explain")

def call_api(customer_id:int, endpoint:str):
    resp = requests.post(endpoint, json={"customer_id": int(customer_id)}, timeout=30)
    js = resp.json()
    if not js.get("ok"):
        raise RuntimeError(js.get("error","Unknown error"))
    return js["data"]

if st.button("Explain my bill"):
    try:
        data = call_api(cid, endpoint)
        st.success(data["message"])

        bp = data["bill_previous"]
        bc = data["bill_current"]

        st.write("**Previous Bill**", pd.DataFrame([bp]))
        st.write("**Current Bill**", pd.DataFrame([bc]))

        st.write("**Diagnostics — Previous Period**", pd.DataFrame([data["previous"]]))
        st.write("**Diagnostics — Current Period**", pd.DataFrame([data["current"]]))

        # --- Causes rendering ---
        st.markdown('### Detected Causes')
        causes = data.get('causes', [])
        if not causes:
            st.info('No specific causes detected with high confidence. Showing general drivers above.')
        else:
            for c in causes:
                st.markdown(f"- **{c['id']}** — {c['message']}  ")
                st.code(json.dumps(c['evidence'], indent=2))

        # --- Charts section (matplotlib) ---
        st.markdown("### Charts")
        intervals = pd.read_csv("../data/intervals_30min.csv", parse_dates=["timestamp"])
        cid_mask = intervals["customer_id"] == int(cid)
        intervals = intervals.loc[cid_mask].copy()

        # Daily kWh for previous period
        prev_start = pd.to_datetime(bp["start_date"])
        prev_end = pd.to_datetime(bp["end_date"])
        prev_slice = intervals[(intervals["timestamp"] >= prev_start) & (intervals["timestamp"] <= prev_end + pd.Timedelta(days=1))].copy()
        prev_daily = prev_slice.groupby(prev_slice["timestamp"].dt.date)["kwh"].sum()

        # Daily kWh for current period
        curr_start = pd.to_datetime(bc["start_date"])
        curr_end = pd.to_datetime(bc["end_date"])
        curr_slice = intervals[(intervals["timestamp"] >= curr_start) & (intervals["timestamp"] <= curr_end + pd.Timedelta(days=1))].copy()
        curr_daily = curr_slice.groupby(curr_slice["timestamp"].dt.date)["kwh"].sum()

        st.caption("Daily kWh — Previous Period")
        fig1, ax1 = plt.subplots()
        ax1.plot(prev_daily.index, prev_daily.values)
        ax1.set_xlabel("Date")
        ax1.set_ylabel("kWh")
        ax1.set_title("Previous Period Daily Usage")
        st.pyplot(fig1)

        st.caption("Daily kWh — Current Period")
        fig2, ax2 = plt.subplots()
        ax2.plot(curr_daily.index, curr_daily.values)
        ax2.set_xlabel("Date")
        ax2.set_ylabel("kWh")
        ax2.set_title("Current Period Daily Usage")
        st.pyplot(fig2)

        st.caption("Temperature vs 30-min kWh — Current Period")
        fig3, ax3 = plt.subplots()
        ax3.scatter(curr_slice["temperature_c"], curr_slice["kwh"], s=4)
        ax3.set_xlabel("Temperature (°C)")
        ax3.set_ylabel("kWh per 30-min")
        ax3.set_title("Temp vs Load (Current)")
        st.pyplot(fig3)

        # --- Virtual Agent mock response-card ---
        st.markdown("### Virtual Agent (Mock) — Response Card Payload")
        response_card = {
            "title": "High Bill Analysis",
            "subtitle": f"Customer {int(cid)} — {bc['start_date']} to {bc['end_date']}",
            "message": data["message"],
            "metrics": {
                "previous_period_kwh": round(float(data["previous"]["total_kwh"]), 2),
                "current_period_kwh": round(float(data["current"]["total_kwh"]), 2),
                "percent_change": round(float(data["percent_change"]), 1)
            },
            "causes": data.get("causes", []),
            "actions": [
                {"type": "link", "label": "View detailed usage", "href": "#"},
                {"type": "postback", "label": "Energy-saving tips", "payload": "show_tips"}
            ]
        }
        st.code(json.dumps(response_card, indent=2))

    except Exception as e:
        st.error(str(e))
