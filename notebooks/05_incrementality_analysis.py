"""Coffee Rewards - Stage 5: timing, incrementality, and reward efficiency.

This module adds the decision-oriented layer missing from the descriptive
funnel analysis. It generates Power BI-ready exports for:

1. Response speed by offer type and event.
2. Reward cost and conversion efficiency by offer type.
3. Within-customer spend and transaction-frequency estimates.
4. A conservative isolated pre/post robustness comparison.

The incrementality outputs are observational estimates, not experimental ROI.
The source data has no gross margin and no randomized control indicator.
"""
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "processed"
EXPORT = ROOT / "data" / "export"
EXPORT.mkdir(parents=True, exist_ok=True)

customers = pd.read_csv(PROCESSED / "customers_clean.csv")
offers = pd.read_csv(PROCESSED / "offers_clean.csv")
events = pd.read_csv(PROCESSED / "events_clean.csv")

REC = "offer received"
VIEW = "offer viewed"
COMP = "offer completed"
TX = "transaction"
OFFER_TYPES = ["bogo", "discount", "informational"]
MAX_TIME = int(events["time"].max())
BIN_HOURS = 6
TIME_BINS = np.arange(0, MAX_TIME + 1, BIN_HOURS)


def build_receipt_journeys():
    """Match response events to individual receipt instances and validity."""
    receipts = (
        events.loc[events["event"] == REC, ["customer_id", "offer_id", "time"]]
        .rename(columns={"time": "rec_time"})
        .reset_index(drop=True)
    )
    receipts["receipt_id"] = receipts.index
    receipts = receipts.merge(
        offers[["offer_id", "offer_type", "duration", "reward", "difficulty"]],
        on="offer_id",
    )
    receipts["expire_time"] = receipts["rec_time"] + receipts["duration"] * 24

    response_events = events.loc[
        events["event"].isin([VIEW, COMP]),
        ["customer_id", "offer_id", "event", "time"],
    ]
    matched = pd.merge_asof(
        response_events.sort_values("time"),
        receipts[
            ["customer_id", "offer_id", "receipt_id", "rec_time", "expire_time"]
        ].sort_values("rec_time"),
        left_on="time",
        right_on="rec_time",
        by=["customer_id", "offer_id"],
        direction="backward",
    )
    matched = matched[matched["time"] <= matched["expire_time"]]
    first_response = (
        matched.sort_values("time")
        .drop_duplicates(["receipt_id", "event"])
        .pivot(index="receipt_id", columns="event", values="time")
        .reset_index()
    )
    journeys = receipts.merge(first_response, on="receipt_id", how="left")
    journeys["time_to_view_h"] = journeys[VIEW] - journeys["rec_time"]
    journeys["time_to_complete_h"] = journeys[COMP] - journeys["rec_time"]
    journeys["time_view_to_complete_h"] = np.where(
        journeys[COMP] >= journeys[VIEW], journeys[COMP] - journeys[VIEW], np.nan
    )
    journeys["completed_flag"] = journeys["time_to_complete_h"].notna()
    return journeys


def export_response_timing(journeys):
    """Export response rate, median, upper quartile, and response thresholds."""
    rows = []
    groups = [("overall", journeys)] + list(journeys.groupby("offer_type"))
    metrics = {
        "view": "time_to_view_h",
        "complete": "time_to_complete_h",
        "view_to_complete": "time_view_to_complete_h",
    }
    for offer_type, group in groups:
        received = len(group)
        for metric, column in metrics.items():
            values = group[column].dropna()
            if values.empty:
                continue
            rows.append(
                {
                    "offer_type": offer_type,
                    "metric": metric,
                    "received": received,
                    "n_events": len(values),
                    "event_rate_pct": round(100 * len(values) / received, 2),
                    "median_h": round(values.median(), 1),
                    "p75_h": round(values.quantile(0.75), 1),
                    "within_24h_pct_received": round(100 * values.le(24).sum() / received, 2),
                    "within_48h_pct_received": round(100 * values.le(48).sum() / received, 2),
                    "within_72h_pct_received": round(100 * values.le(72).sum() / received, 2),
                }
            )
    output = pd.DataFrame(rows)
    output.to_csv(EXPORT / "response_timing.csv", index=False)
    return output


def export_reward_efficiency(journeys):
    """Compare conversion volume with the face value of issued rewards."""
    received = (
        events.loc[events["event"] == REC]
        .merge(offers[["offer_id", "offer_type"]], on="offer_id")
        .groupby("offer_type")
        .size()
    )
    completed_events = events.loc[events["event"] == COMP].merge(
        offers[["offer_id", "offer_type", "reward"]].rename(
            columns={"reward": "offer_reward"}
        ),
        on="offer_id",
    )
    completed_summary = completed_events.groupby("offer_type")["offer_reward"].agg(
        completed="size", total_reward_usd="sum"
    )
    rows = []
    total_completed = int(completed_summary["completed"].sum())
    total_cost = float(completed_summary["total_reward_usd"].sum())
    for offer_type in OFFER_TYPES:
        n_received = int(received.get(offer_type, 0))
        n_completed = int(completed_summary.loc[offer_type, "completed"]) \
            if offer_type in completed_summary.index else 0
        reward_cost = float(completed_summary.loc[offer_type, "total_reward_usd"]) \
            if offer_type in completed_summary.index else 0.0
        rows.append(
            {
                "offer_type": offer_type,
                "received": n_received,
                "completed": n_completed,
                "completion_rate_pct": round(100 * n_completed / n_received, 2),
                "total_reward_usd": round(reward_cost, 2),
                "avg_reward_per_completion_usd": round(
                    reward_cost / n_completed, 2
                ) if n_completed else 0.0,
                "reward_cost_per_received_usd": round(reward_cost / n_received, 2),
                "completion_share_pct": round(
                    100 * n_completed / total_completed, 2
                ) if total_completed else 0.0,
                "reward_cost_share_pct": round(
                    100 * reward_cost / total_cost, 2
                ) if total_cost else 0.0,
            }
        )
    output = pd.DataFrame(rows)
    output.to_csv(EXPORT / "reward_efficiency.csv", index=False)
    return output


def build_customer_time_panel():
    """Create a balanced customer-by-six-hour panel for fixed-effects analysis."""
    customer_ids = customers["customer_id"].unique()
    customer_index = {customer_id: i for i, customer_id in enumerate(customer_ids)}
    n_customers = len(customer_ids)
    n_bins = len(TIME_BINS)

    spend = np.zeros((n_customers, n_bins), dtype=float)
    tx_count = np.zeros((n_customers, n_bins), dtype=float)
    transactions = events[events["event"] == TX]
    for row in transactions.itertuples():
        bin_index = int(row.time // BIN_HOURS)
        if bin_index < n_bins:
            customer_row = customer_index[row.customer_id]
            spend[customer_row, bin_index] += row.amount
            tx_count[customer_row, bin_index] += 1

    receipts = (
        events.loc[events["event"] == REC, ["customer_id", "offer_id", "time"]]
        .merge(offers[["offer_id", "offer_type", "duration"]], on="offer_id")
    )
    exposures = {}
    for offer_type in OFFER_TYPES:
        changes = np.zeros((n_customers, n_bins + 1), dtype=np.int16)
        for row in receipts[receipts["offer_type"] == offer_type].itertuples():
            customer_row = customer_index[row.customer_id]
            start = int(row.time // BIN_HOURS)
            end = min(int((row.time + row.duration * 24) // BIN_HOURS), n_bins - 1)
            changes[customer_row, start] += 1
            if end + 1 < n_bins:
                changes[customer_row, end + 1] -= 1
        exposures[offer_type] = (np.cumsum(changes[:, :-1], axis=1) > 0).astype(float)

    return customer_ids, spend, tx_count, exposures


def two_way_demean(values):
    """Remove customer and time means from a balanced panel."""
    return (
        values
        - values.mean(axis=1, keepdims=True)
        - values.mean(axis=0, keepdims=True)
        + values.mean()
    ).ravel()


def export_fixed_effects_incrementality(spend, tx_count, exposures, reward_efficiency):
    """Estimate within-customer changes while controlling for time-bin effects."""
    x = np.column_stack([two_way_demean(exposures[t]) for t in OFFER_TYPES])
    spend_beta = np.linalg.lstsq(x, two_way_demean(spend), rcond=None)[0]
    tx_beta = np.linalg.lstsq(x, two_way_demean(tx_count), rcond=None)[0]
    informational_spend = spend_beta[OFFER_TYPES.index("informational")]
    informational_tx = tx_beta[OFFER_TYPES.index("informational")]
    reward_lookup = reward_efficiency.set_index("offer_type")["total_reward_usd"]

    rows = []
    for i, offer_type in enumerate(OFFER_TYPES):
        exposed_bins = int(exposures[offer_type].sum())
        reward_cost = float(reward_lookup.get(offer_type, 0.0))
        estimated_sales = float(spend_beta[i] * exposed_bins)
        benchmark_adjusted_sales = float(
            (spend_beta[i] - informational_spend) * exposed_bins
        )
        rows.append(
            {
                "offer_type": offer_type,
                "active_customer_periods_6h": exposed_bins,
                "estimated_spend_change_per_day_usd": round(spend_beta[i] * 4, 2),
                "estimated_tx_change_per_day": round(tx_beta[i] * 4, 3),
                "estimated_incremental_sales_usd": round(estimated_sales, 2),
                "vs_informational_spend_change_per_day_usd": round(
                    (spend_beta[i] - informational_spend) * 4, 2
                ),
                "vs_informational_tx_change_per_day": round(
                    (tx_beta[i] - informational_tx) * 4, 3
                ),
                "vs_informational_incremental_sales_usd": round(
                    benchmark_adjusted_sales, 2
                ),
                "total_reward_usd": round(reward_cost, 2),
                "sales_per_reward_usd": round(
                    benchmark_adjusted_sales / reward_cost, 2
                ) if reward_cost and benchmark_adjusted_sales > 0 else np.nan,
                "break_even_margin_pct": round(
                    100 * reward_cost / benchmark_adjusted_sales, 2
                ) if reward_cost and benchmark_adjusted_sales > 0 else np.nan,
            }
        )
    output = pd.DataFrame(rows)
    output.to_csv(EXPORT / "incrementality_fixed_effects.csv", index=False)
    return output


def export_isolated_pre_post(customer_ids, spend, tx_count, journeys):
    """Compare equal pre/active windows for receipts isolated from other offers."""
    n_bins = spend.shape[1]
    customer_index = {customer_id: i for i, customer_id in enumerate(customer_ids)}
    receipts = journeys.copy()
    receipts["start_bin"] = (receipts["rec_time"] // BIN_HOURS).astype(int)
    receipts["duration_bins"] = (receipts["duration"] * 24 // BIN_HOURS).astype(int)
    receipts["end_bin"] = receipts["start_bin"] + receipts["duration_bins"]

    isolated = {}
    for _, group in receipts.groupby("customer_id"):
        for index, row in group.iterrows():
            if row["start_bin"] - row["duration_bins"] < 0 or row["end_bin"] > n_bins:
                isolated[index] = False
                continue
            others = group.drop(index)
            combined_start = row["start_bin"] - row["duration_bins"]
            overlap = (
                (others["start_bin"] < row["end_bin"])
                & (others["end_bin"] > combined_start)
            ).any()
            isolated[index] = not overlap
    receipts["isolated"] = receipts.index.map(isolated).fillna(False)

    spend_cumulative = np.pad(np.cumsum(spend, axis=1), ((0, 0), (1, 0)))
    tx_cumulative = np.pad(np.cumsum(tx_count, axis=1), ((0, 0), (1, 0)))
    rows = []
    for row in receipts[receipts["isolated"]].itertuples():
        customer_row = customer_index[row.customer_id]
        pre_start = row.start_bin - row.duration_bins
        active_start = row.start_bin
        active_end = row.end_bin
        pre_spend = spend_cumulative[customer_row, active_start] - spend_cumulative[
            customer_row, pre_start
        ]
        active_spend = spend_cumulative[customer_row, active_end] - spend_cumulative[
            customer_row, active_start
        ]
        pre_tx = tx_cumulative[customer_row, active_start] - tx_cumulative[
            customer_row, pre_start
        ]
        active_tx = tx_cumulative[customer_row, active_end] - tx_cumulative[
            customer_row, active_start
        ]
        rows.append(
            {
                "offer_type": row.offer_type,
                "duration_days": row.duration,
                "pre_spend_usd": pre_spend,
                "active_spend_usd": active_spend,
                "pre_tx": pre_tx,
                "active_tx": active_tx,
                "reward_cost_usd": row.reward if row.completed_flag else 0.0,
            }
        )
    paired = pd.DataFrame(rows)
    paired["spend_change_usd"] = paired["active_spend_usd"] - paired["pre_spend_usd"]
    paired["tx_change"] = paired["active_tx"] - paired["pre_tx"]
    paired["spend_change_per_day_usd"] = paired["spend_change_usd"] / paired["duration_days"]
    paired["tx_change_per_day"] = paired["tx_change"] / paired["duration_days"]

    output = (
        paired.groupby("offer_type")
        .agg(
            n_isolated_receipts=("offer_type", "size"),
            avg_duration_days=("duration_days", "mean"),
            avg_pre_spend_usd=("pre_spend_usd", "mean"),
            avg_active_spend_usd=("active_spend_usd", "mean"),
            avg_spend_change_usd=("spend_change_usd", "mean"),
            avg_spend_change_per_day_usd=("spend_change_per_day_usd", "mean"),
            avg_pre_tx=("pre_tx", "mean"),
            avg_active_tx=("active_tx", "mean"),
            avg_tx_change_per_day=("tx_change_per_day", "mean"),
            avg_reward_cost_per_receipt_usd=("reward_cost_usd", "mean"),
        )
        .round(2)
        .reset_index()
    )
    output.to_csv(EXPORT / "incrementality_pre_post.csv", index=False)
    return output


def export_powerbi_long(response_timing, reward_efficiency, fixed_effects):
    """Export the new metrics in the report's generic five-column schema."""
    timing = response_timing[
        response_timing["offer_type"].isin(["bogo", "discount", "informational"])
        & response_timing["metric"].isin(["view", "complete"])
    ].copy()
    timing["measure"] = "median_time_to_" + timing["metric"] + "_h"
    timing = timing.rename(columns={"offer_type": "category", "median_h": "value"})
    timing["dataset"] = "response_timing"
    timing["dimension"] = "offer_type"

    reward_columns = [
        "completion_share_pct",
        "reward_cost_share_pct",
        "reward_cost_per_received_usd",
        "total_reward_usd",
    ]
    reward = reward_efficiency.melt(
        id_vars="offer_type",
        value_vars=reward_columns,
        var_name="measure",
        value_name="value",
    ).rename(columns={"offer_type": "category"})
    reward["dataset"] = "reward_efficiency"
    reward["dimension"] = "offer_type"

    model_columns = [
        "vs_informational_spend_change_per_day_usd",
        "vs_informational_tx_change_per_day",
        "sales_per_reward_usd",
        "break_even_margin_pct",
    ]
    modeled = fixed_effects[fixed_effects["offer_type"].isin(["bogo", "discount"])].melt(
        id_vars="offer_type",
        value_vars=model_columns,
        var_name="measure",
        value_name="value",
    ).rename(columns={"offer_type": "category"})
    modeled["dataset"] = "incrementality_model"
    modeled["dimension"] = "offer_type"

    output = pd.concat([timing, reward, modeled], ignore_index=True)
    output = output[["dataset", "dimension", "category", "measure", "value"]]
    output.to_csv(EXPORT / "powerbi_additional_metrics.csv", index=False)
    return output


journeys = build_receipt_journeys()
response_timing = export_response_timing(journeys)
reward_efficiency = export_reward_efficiency(journeys)
customer_ids, spend, tx_count, exposures = build_customer_time_panel()
fixed_effects = export_fixed_effects_incrementality(
    spend, tx_count, exposures, reward_efficiency
)
pre_post = export_isolated_pre_post(customer_ids, spend, tx_count, journeys)
powerbi_long = export_powerbi_long(response_timing, reward_efficiency, fixed_effects)

print("\nResponse timing")
print(response_timing.to_string(index=False))
print("\nReward efficiency")
print(reward_efficiency.to_string(index=False))
print("\nWithin-customer fixed-effects estimates")
print(fixed_effects.to_string(index=False))
print("\nIsolated pre/post robustness check")
print(pre_post.to_string(index=False))
print("\nPower BI additional metrics")
print(powerbi_long.to_string(index=False))
print("\nExports generated in data/export/.")
