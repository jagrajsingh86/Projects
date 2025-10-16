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

def _add_hdd_cdd(df):
    df = df.copy()
    df["hour"] = df["timestamp"].dt.hour
    df["date"] = df["timestamp"].dt.date
    df["HDD"] = (16 - df["temperature_c"]).clip(lower=0)
    df["CDD"] = (df["temperature_c"] - 26).clip(lower=0)
    return df

def compute_summary(intervals_period):
    ip = _add_hdd_cdd(intervals_period)
    total_kwh = ip["kwh"].sum()
    daily = ip.groupby("date")["kwh"].sum() if len(ip) else pd.Series(dtype=float)
    avg_daily = daily.mean() if len(daily) else 0.0
    corr_h = np.corrcoef(ip["HDD"], ip["kwh"])[0,1] if len(ip)>2 else np.nan
    corr_c = np.corrcoef(ip["CDD"], ip["kwh"])[0,1] if len(ip)>2 else np.nan
    evening_mask = ip["hour"].between(17, 21)
    evening_share = ip.loc[evening_mask, "kwh"].sum() / max(total_kwh, 1e-6) if total_kwh>0 else 0.0
    base_load = float(np.percentile(ip["kwh"], 5)) if len(ip) else 0.0
    ip["weekday"] = ip["timestamp"].dt.weekday if len(ip) else 0
    day_mask = (ip["hour"]>=9) & (ip["hour"]<17) & (ip["weekday"]<5) if len(ip) else []
    weekday_day_share = ip.loc[day_mask, "kwh"].sum() / max(total_kwh, 1e-6) if total_kwh>0 and len(ip) else 0.0
    return {
        "total_kwh": float(total_kwh),
        "avg_daily_kwh": float(avg_daily) if not np.isnan(avg_daily) else 0.0,
        "corr_heating": float(corr_h) if not np.isnan(corr_h) else 0.0,
        "corr_cooling": float(corr_c) if not np.isnan(corr_c) else 0.0,
        "evening_peak_share": float(evening_share),
        "base_load_kwh_30m": float(base_load),
        "weekday_day_share": float(weekday_day_share)
    }

def explain_change(prev_sum, curr_sum):
    change = (curr_sum["total_kwh"] - prev_sum["total_kwh"]) / max(prev_sum["total_kwh"], 1e-6)
    drivers = []
    if curr_sum["corr_heating"] > 0.25 and curr_sum["corr_heating"] > curr_sum["corr_cooling"]:
        drivers.append("increased heating usage on colder days")
    if curr_sum["corr_cooling"] > 0.25 and curr_sum["corr_cooling"] >= curr_sum["corr_heating"]:
        drivers.append("increased cooling usage on hotter days")
    if curr_sum["evening_peak_share"] - prev_sum["evening_peak_share"] > 0.05:
        drivers.append("higher evening peak consumption")
    if not drivers:
        drivers.append("general increase in daily consumption")
    pct = round(change*100, 1)
    return pct, drivers

def _long_runs(series_bool):
    max_run = 0
    run = 0
    runs_ge3 = 0
    for v in series_bool:
        if v:
            run += 1
            max_run = max(max_run, run)
        else:
            if run >= 3:
                runs_ge3 += 1
            run = 0
    if run >= 3:
        runs_ge3 += 1
    return max_run, runs_ge3

def detect_ev(curr_slice):
    ip = _add_hdd_cdd(curr_slice)
    mask = (ip["hour"]>=21) | (ip["hour"]<7)
    night = ip.loc[mask].copy()
    if night.empty:
        return False, {}
    thr = 3.0
    nights_with_plateau = 0
    for d, g in night.groupby("date"):
        max_run, _ = _long_runs(g["kwh"] >= thr)
        if max_run >= 3:
            nights_with_plateau += 1
    return nights_with_plateau >= 5, {"nights_with_plateau": int(nights_with_plateau), "threshold_kwh_30m": thr}

def detect_pool(curr_slice):
    ip = _add_hdd_cdd(curr_slice)
    day = ip[(ip["hour"]>=8) & (ip["hour"]<=18)].copy()
    if day.empty:
        return False, {}
    days_with_plateau = 0
    for d, g in day.groupby("date"):
        max_run, _ = _long_runs(g["kwh"] >= 0.6)
        if max_run >= 6:
            days_with_plateau += 1
    return days_with_plateau >= 15, {"days_with_plateau": int(days_with_plateau)}

def detect_weather_driven(prev_slice, curr_slice):
    sp = compute_summary(prev_slice)
    sc = compute_summary(curr_slice)
    delta = (sc["total_kwh"] - sp["total_kwh"]) / max(sp["total_kwh"], 1e-6) * 100.0
    if sc["corr_heating"] >= 0.25 and sc["corr_heating"] > sc["corr_cooling"] and delta >= 10:
        return ("heating_weather_driven", "Colder days increased heating use", {"corr_heating": round(sc["corr_heating"],2), "delta_pct": round(delta,1)})
    if sc["corr_cooling"] >= 0.25 and sc["corr_cooling"] >= sc["corr_heating"] and delta >= 10:
        return ("cooling_weather_driven", "Hotter days increased cooling use", {"corr_cooling": round(sc["corr_cooling"],2), "delta_pct": round(delta,1)})
    return None

def detect_daytime_occupancy(prev_slice, curr_slice):
    sp = compute_summary(prev_slice)
    sc = compute_summary(curr_slice)
    lift = (sc["weekday_day_share"] - sp["weekday_day_share"]) * 100.0
    if lift >= 5.0 and (sc["total_kwh"] - sp["total_kwh"]) > 0:
        return True, {"weekday_day_share_delta_pts": round(lift,1)}
    return False, {}

def detect_solar_offline(prev_slice, curr_slice, solar_flag):
    if not solar_flag:
        return False, {}
    prev = _add_hdd_cdd(prev_slice)
    curr = _add_hdd_cdd(curr_slice)
    prev_mid = prev[(prev["hour"]>=10) & (prev["hour"]<=15)]["kwh"].mean()
    curr_mid = curr[(curr["hour"]>=10) & (curr["hour"]<=15)]["kwh"].mean()
    if pd.isna(prev_mid) or pd.isna(curr_mid) or prev_mid<=0:
        return False, {}
    if curr_mid >= prev_mid * 1.4:
        return True, {"midday_import_ratio": round(curr_mid/prev_mid,2)}
    return False, {}

def assemble_causes(customer_id, customers, prev_slice, curr_slice):
    causes = []
    ev_yes, ev_ev = detect_ev(curr_slice)
    if ev_yes:
        causes.append({"id":"ev_charging","confidence":"high","evidence":ev_ev,"message":"Likely EV charging most nights increased overnight usage."})
    pool_yes, pool_ev = detect_pool(curr_slice)
    if pool_yes:
        causes.append({"id":"pool_pump","confidence":"medium","evidence":pool_ev,"message":"Regular daytime plateau suggests a pool pump schedule increasing usage."})
    wd = detect_weather_driven(prev_slice, curr_slice)
    if wd:
        cid, msg, ev = wd
        conf = "medium" if "delta_pct" in ev and ev["delta_pct"]<20 else "high"
        causes.append({"id":cid,"confidence":conf,"evidence":ev,"message":msg})
    occ_yes, occ_ev = detect_daytime_occupancy(prev_slice, curr_slice)
    if occ_yes:
        causes.append({"id":"daytime_occupancy","confidence":"medium","evidence":occ_ev,"message":"Weekday daytime usage is higher, suggesting more time at home or guests."})
    solar_flag = False
    try:
        solar_flag = bool(customers.loc[customers["customer_id"]==customer_id, "solar_pv"].iloc[0])
    except Exception:
        solar_flag = False
    sol_yes, sol_ev = detect_solar_offline(prev_slice, curr_slice, solar_flag)
    if sol_yes:
        causes.append({"id":"solar_offline","confidence":"medium","evidence":sol_ev,"message":"Daytime grid import increased; solar system may be offline or underperforming."})
    return causes

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
    causes = assemble_causes(customer_id, customers, i_prev, i_curr)
    return {
        "previous": s_prev,
        "current": s_curr,
        "percent_change": pct,
        "drivers": drivers,
        "causes": causes,
        "message": explanation + detail
    }
