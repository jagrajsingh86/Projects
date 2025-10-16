import pandas as pd
import numpy as np
from datetime import datetime
from dateutil import parser as dparser

def load_data(data_dir="../data"):
    customers = pd.read_csv(f"{data_dir}/customers.csv")
    bills = pd.read_csv(f"{data_dir}/bills.csv", parse_dates=["start_date","end_date"])
    intervals = pd.read_csv(f"{data_dir}/intervals_30min.csv", parse_dates=["timestamp"])
    return customers, bills, intervals

def period_slice(intervals, start, end):
    m = (intervals["timestamp"] >= pd.Timestamp(start)) & (intervals["timestamp"] <= pd.Timestamp(end) + pd.Timedelta(days=1) - pd.Timedelta(minutes=30))
    return intervals.loc[m].copy()

def compute_summary(intervals_period):
    total_kwh = intervals_period["kwh"].sum()
    avg_daily = intervals_period.groupby(intervals_period["timestamp"].dt.date)["kwh"].sum().mean()
    # temperature correlation
    # Heating degree proxy:  max(0, 16 - temp); Cooling degree proxy: max(0, temp - 26)
    hdd = np.maximum(0, 16 - intervals_period["temperature_c"])
    cdd = np.maximum(0, intervals_period["temperature_c"] - 26)
    corr_h = np.corrcoef(hdd, intervals_period["kwh"])[0,1]
    corr_c = np.corrcoef(cdd, intervals_period["kwh"])[0,1]
    evening_mask = intervals_period["timestamp"].dt.hour.between(17, 21)
    evening_share = intervals_period.loc[evening_mask, "kwh"].sum() / max(total_kwh, 1e-6)
    return {
        "total_kwh": float(total_kwh),
        "avg_daily_kwh": float(avg_daily),
        "corr_heating": float(corr_h) if not np.isnan(corr_h) else 0.0,
        "corr_cooling": float(corr_c) if not np.isnan(corr_c) else 0.0,
        "evening_peak_share": float(evening_share)
    }

def explain_change(prev_sum, curr_sum):
    change = (curr_sum["total_kwh"] - prev_sum["total_kwh"]) / max(prev_sum["total_kwh"], 1e-6)
    drivers = []
    if curr_sum["corr_heating"] > 0.2 and curr_sum["corr_heating"] > curr_sum["corr_cooling"]:
        drivers.append("increased heating usage on colder days")
    if curr_sum["corr_cooling"] > 0.2 and curr_sum["corr_cooling"] >= curr_sum["corr_heating"]:
        drivers.append("increased cooling usage on hotter days")
    if curr_sum["evening_peak_share"] - prev_sum["evening_peak_share"] > 0.05:
        drivers.append("higher evening peak consumption")
    if not drivers:
        drivers.append("general increase in daily consumption")
    pct = round(change*100, 1)
    return pct, drivers

def generate_explanation(customer_id, customers, bills, intervals):
    b_prev = bills[(bills["customer_id"]==customer_id) & (bills["period"]=="previous")].iloc[0]
    b_curr = bills[(bills["customer_id"]==customer_id) & (bills["period"]=="current")].iloc[0]
    i_prev = period_slice(intervals, b_prev["start_date"], b_prev["end_date"])
    i_curr = period_slice(intervals, b_curr["start_date"], b_curr["end_date"])
    s_prev = compute_summary(i_prev)
    s_curr = compute_summary(i_curr)
    pct, drivers = explain_change(s_prev, s_curr)
    explanation = f"Your energy use increased by {pct}% compared to the previous bill period."
    if pct < 0:
        explanation = f"Your energy use decreased by {abs(pct)}% compared to the previous bill period."
    detail = " Likely drivers: " + "; ".join(drivers) + "."
    return {
        "previous": s_prev,
        "current": s_curr,
        "percent_change": pct,
        "drivers": drivers,
        "message": explanation + detail
    }
