"""Coffee Rewards - Stage 4: export Power BI-ready datasets.

Genera de forma reproducible:
  1. Diagnóstico de la cohorte sin demografía.
  2. `data/processed/offers_long.csv` (explode definitivo de `channels`).
  3. Pre-aggregated tables in `data/export/` ready for Power BI.

No modifica `data/raw/`. Los números se recalculan desde `data/processed/` y
deben coincidir con los hallazgos de la Etapa 3 (spec business-questions).
"""
import json
import os

import numpy as np
import pandas as pd

customers = pd.read_csv("data/processed/customers_clean.csv")
offers = pd.read_csv("data/processed/offers_clean.csv")
events = pd.read_csv("data/processed/events_clean.csv")

customers["has_demographics"] = (
    customers["has_demographics"].astype(str).str.lower().isin(["true", "1"])
)

REC = "offer received"
VIEW = "offer viewed"
COMP = "offer completed"
TX = "transaction"

# ==============================================================================
# 0. Diagnóstico — cohorte sin demografía
# ==============================================================================
print("=" * 70)
print("0. DIAGNOSTICO — cohorte sin demografia")
print("=" * 70)
nodemo = customers[~customers["has_demographics"]]
print(f"clientes: {len(nodemo)}")
print(f"became_member_on: {nodemo['became_member_on'].min()} .. "
      f"{nodemo['became_member_on'].max()}  ({nodemo['became_member_on'].nunique()} fechas unicas)")
print("top fechas de alta:")
print(nodemo["became_member_on"].value_counts().head(5).to_string())

ev_nodemo = events.merge(customers[["customer_id", "has_demographics"]], on="customer_id")
ev_nodemo = ev_nodemo[~ev_nodemo["has_demographics"]]
print("\neventos por tipo (sin demo):")
print(ev_nodemo["event"].value_counts().to_string())

tx = ev_nodemo[ev_nodemo["event"] == TX]
print("\ntransacciones (sin demo):")
print(f"  n={len(tx)}  media={tx['amount'].mean():.2f} USD  "
      f"mediana={tx['amount'].median():.2f}  min={tx['amount'].min():.2f}  "
      f"max={tx['amount'].max():.2f}")
print(f"  <= 1 USD: {(tx['amount'] <= 1).sum()} ({(tx['amount'] <= 1).mean() * 100:.1f}%)")
print(f"  tiempo (h): min={tx['time'].min()} max={tx['time'].max()} "
      f"media={tx['time'].mean():.1f}")

# ==============================================================================
# 1. offers_long (explode definitivo)
# ==============================================================================
def parse_channels(s):
    try:
        return json.loads(s)
    except Exception:
        return []

offers["_ch"] = offers["channels"].apply(parse_channels)
offers_long = (
    offers.explode("_ch")
    .rename(columns={"_ch": "channel"})[["offer_id", "offer_type", "channel"]]
    .reset_index(drop=True)
)
offers_long.to_csv("data/processed/offers_long.csv", index=False)
print("\n" + "=" * 70)
print("1. offers_long.csv")
print("=" * 70)
print(f"filas: {len(offers_long)}")
print(offers_long["channel"].value_counts().to_string())

# ==============================================================================
# 2. Exports pre-agregados
# ==============================================================================
os.makedirs("data/export", exist_ok=True)
print("\n" + "=" * 70)
print("2. EXPORTS (data/export/)")
print("=" * 70)

# ---- funnel_overall (Q1/Q2) ----
rec = (events["event"] == REC).sum()
view = (events["event"] == VIEW).sum()
comp = (events["event"] == COMP).sum()
funnel = pd.DataFrame({
    "stage": [REC, VIEW, COMP],
    "count": [rec, view, comp],
    "pct_of_received": [100.0, round(100 * view / rec, 2), round(100 * comp / rec, 2)],
})
funnel.to_csv("data/export/funnel_overall.csv", index=False)
print("\nfunnel_overall.csv"); print(funnel.to_string(index=False))

# ---- funnel_by_type (Q3) ----
ft = (
    events[events["event"].isin([REC, VIEW, COMP])]
    .merge(offers[["offer_id", "offer_type"]], on="offer_id")
)
fbt = ft.groupby("offer_type")["event"].value_counts().unstack(fill_value=0)
for c in [REC, VIEW, COMP]:
    if c not in fbt.columns:
        fbt[c] = 0
fbt = fbt.rename(columns={REC: "received", VIEW: "viewed", COMP: "completed"}).reset_index()
fbt["view_rate_pct"] = round(100 * fbt["viewed"] / fbt["received"], 2)
fbt["completion_rate_pct"] = round(100 * fbt["completed"] / fbt["received"], 2)
fbt.to_csv("data/export/funnel_by_type.csv", index=False)
print("\nfunnel_by_type.csv"); print(fbt.to_string(index=False))

# ---- funnel_by_channel (Q4) ----
evch = (
    events[events["event"].isin([REC, VIEW, COMP])]
    .merge(offers_long[["offer_id", "channel"]], on="offer_id")
)
n_offers = offers_long.groupby("channel")["offer_id"].nunique()
fbc = evch.groupby("channel")["event"].value_counts().unstack(fill_value=0)
for c in [REC, VIEW, COMP]:
    if c not in fbc.columns:
        fbc[c] = 0
fbc = fbc.rename(columns={REC: "received", VIEW: "viewed", COMP: "completed"})
fbc["n_offers"] = n_offers
fbc = fbc.reset_index()
fbc["view_rate_pct"] = round(100 * fbc["viewed"] / fbc["received"], 2)
fbc["completion_rate_pct"] = round(100 * fbc["completed"] / fbc["received"], 2)
fbc = fbc[["channel", "n_offers", "received", "viewed", "completed",
           "view_rate_pct", "completion_rate_pct"]].sort_values("completion_rate_pct", ascending=False)
fbc.to_csv("data/export/funnel_by_channel.csv", index=False)
print("\nfunnel_by_channel.csv"); print(fbc.to_string(index=False))

# ---- time_to_event (Q5) ----
# A customer can receive the same offer more than once. Match each view and
# completion to the latest eligible receipt instance instead of collapsing the
# entire customer-offer history into one pair.
receipts5 = (
    events.loc[events["event"] == REC, ["customer_id", "offer_id", "time"]]
    .rename(columns={"time": "rec_time"})
    .reset_index(drop=True)
)
receipts5["receipt_id"] = receipts5.index
receipts5 = receipts5.merge(
    offers[["offer_id", "offer_type", "duration"]], on="offer_id"
)
receipts5["expire_time"] = receipts5["rec_time"] + receipts5["duration"] * 24

response_events = events.loc[
    events["event"].isin([VIEW, COMP]),
    ["customer_id", "offer_id", "event", "time"],
]
matched_events = pd.merge_asof(
    response_events.sort_values("time"),
    receipts5[
        ["customer_id", "offer_id", "receipt_id", "rec_time", "expire_time"]
    ].sort_values("rec_time"),
    left_on="time",
    right_on="rec_time",
    by=["customer_id", "offer_id"],
    direction="backward",
)
matched_events = matched_events[matched_events["time"] <= matched_events["expire_time"]]
first_response = (
    matched_events.sort_values("time")
    .drop_duplicates(["receipt_id", "event"])
    .pivot(index="receipt_id", columns="event", values="time")
    .reset_index()
)
pairs = receipts5.merge(first_response, on="receipt_id", how="left")
pairs["time_to_view"] = pairs[VIEW] - pairs["rec_time"]
pairs["time_to_complete"] = pairs[COMP] - pairs["rec_time"]
tte_rows = []
for typ, grp in pairs.groupby("offer_type"):
    for metric in ["time_to_view", "time_to_complete"]:
        s = grp[metric].dropna()
        tte_rows.append({
            "offer_type": typ,
            "metric": metric,
            "n": len(s),
            "mean_h": round(s.mean(), 1),
            "median_h": round(s.median(), 1),
        })
tte = pd.DataFrame(tte_rows)
tte = tte[tte["n"] > 0].reset_index(drop=True)  # informativo no tiene tiempo-de-completar
tte.to_csv("data/export/time_to_event.csv", index=False)
print("\ntime_to_event.csv"); print(tte.to_string(index=False))

# ---- spend_by_context (Q6) ----
offers["dur_h"] = offers["duration"] * 24
trans = events.loc[events["event"] == TX, ["customer_id", "time", "amount"]].reset_index(drop=True)
trans["tx_id"] = trans.index
rec_e = (
    events.loc[events["event"] == REC, ["customer_id", "offer_id", "time"]]
    .rename(columns={"time": "rec_time"})
    .merge(offers[["offer_id", "dur_h"]], on="offer_id")
)
rec_e["expire"] = rec_e["rec_time"] + rec_e["dur_h"]
view_e = events.loc[events["event"] == VIEW, ["customer_id", "offer_id", "time"]].rename(columns={"time": "view_time"})
active = trans.merge(rec_e[["customer_id", "offer_id", "rec_time", "expire"]], on="customer_id").query("time >= rec_time and time <= expire")
active_v = active.merge(view_e, on=["customer_id", "offer_id"]).query("view_time >= rec_time and view_time <= time")
tx_active = active["tx_id"].drop_duplicates()
tx_active_viewed = active_v["tx_id"].drop_duplicates()
trans["context"] = "sin_oferta_activa"
trans.loc[trans["tx_id"].isin(tx_active), "context"] = "oferta_activa_no_vista"
trans.loc[trans["tx_id"].isin(tx_active_viewed), "context"] = "oferta_activa_vista"
sbc = (
    trans.groupby("context")["amount"]
    .agg(n="count", avg_amount_usd="mean", total_usd="sum")
    .round(2)
    .reindex(["sin_oferta_activa", "oferta_activa_no_vista", "oferta_activa_vista"])
    .reset_index()
)
sbc.to_csv("data/export/spend_by_context.csv", index=False)
print("\nspend_by_context.csv"); print(sbc.to_string(index=False))

# ---- completion_by_segment (Q7) ----
ev7 = (
    events[events["event"].isin([REC, COMP])]
    .merge(customers[["customer_id", "gender", "age", "income", "has_demographics"]], on="customer_id")
)
ev7 = ev7[ev7["has_demographics"]]
ev7["age_bin"] = pd.cut(ev7["age"], bins=[0, 30, 40, 50, 60, 70, 200],
                        labels=["<30", "30-39", "40-49", "50-59", "60-69", "70+"], right=False)
ev7["income_bin"] = pd.cut(ev7["income"], bins=[0, 40000, 60000, 80000, 100000, 200000],
                           labels=["<40k", "40-59k", "60-79k", "80-99k", "100k+"], right=False)


def seg_table(df, dim, segcol):
    out = df.groupby(segcol).apply(lambda g: pd.Series({
        "received": (g["event"] == REC).sum(),
        "completed": (g["event"] == COMP).sum(),
    })).reset_index()
    out.columns = [segcol, "received", "completed"]
    out["completion_rate_pct"] = round(100 * out["completed"] / out["received"], 2)
    out["dimension"] = dim
    out = out.rename(columns={segcol: "segment"})
    return out[["dimension", "segment", "received", "completed", "completion_rate_pct"]]


cbs = pd.concat([
    seg_table(ev7, "age", "age_bin"),
    seg_table(ev7, "income", "income_bin"),
    seg_table(ev7, "gender", "gender"),
], ignore_index=True)
cbs.to_csv("data/export/completion_by_segment.csv", index=False)
print("\ncompletion_by_segment.csv"); print(cbs.to_string(index=False))

# ---- cohort_comparison (Q8) ----
ev8 = (
    events[events["event"].isin([REC, VIEW, COMP])]
    .merge(customers[["customer_id", "has_demographics"]], on="customer_id")
)


def funnel_rates(g):
    return pd.Series({
        "received": (g["event"] == REC).sum(),
        "viewed": (g["event"] == VIEW).sum(),
        "completed": (g["event"] == COMP).sum(),
    })


cc = ev8.groupby("has_demographics").apply(funnel_rates).reset_index()
cc["view_rate_pct"] = round(100 * cc["viewed"] / cc["received"], 2)
cc["completion_rate_pct"] = round(100 * cc["completed"] / cc["received"], 2)
trans8 = events[events["event"] == TX].merge(customers[["customer_id", "has_demographics"]], on="customer_id")
tx8 = trans8.groupby("has_demographics")["amount"].agg(n_tx="count", avg_ticket_usd="mean").round(2).reset_index()
cc = cc.merge(tx8, on="has_demographics")
cc["cohort"] = np.where(cc["has_demographics"], "con_demografia", "sin_demografia")
cc = cc[["cohort", "received", "viewed", "completed", "view_rate_pct",
         "completion_rate_pct", "n_tx", "avg_ticket_usd"]]
cc.to_csv("data/export/cohort_comparison.csv", index=False)
print("\ncohort_comparison.csv"); print(cc.to_string(index=False))

# ---- reward_value (Q9) ----
completed = events[events["event"] == COMP].merge(
    offers[["offer_id", "offer_type", "reward"]], on="offer_id", suffixes=("", "_off")
)
rv = (
    completed.groupby("offer_type")["reward_off"]
    .agg(n_completed="count", total_reward_usd="sum", avg_reward_usd="mean")
    .round(2)
    .reset_index()
    .reindex([0, 1, 2])
)
# asegurar que informational aparezca con 0
for t in ["bogo", "discount", "informational"]:
    if t not in rv["offer_type"].values:
        rv = pd.concat([rv, pd.DataFrame([{"offer_type": t, "n_completed": 0,
                                           "total_reward_usd": 0.0, "avg_reward_usd": 0.0}])],
                       ignore_index=True)
rv = rv[rv["offer_type"].isin(["bogo", "discount", "informational"])].reset_index(drop=True)
rv["n_completed"] = rv["n_completed"].astype(int)
rv.to_csv("data/export/reward_value.csv", index=False)
print("\nreward_value.csv"); print(rv.to_string(index=False))

print("\n" + "=" * 70)
print("Exports generados correctamente en data/export/")
print("=" * 70)
