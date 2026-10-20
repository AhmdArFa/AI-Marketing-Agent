"""Pandas campaign analytics. Pure functions, no side effects, fully testable."""

from typing import Any, Dict, List

import pandas as pd


def _safe_rate(numerator: float, denominator: float) -> float:
    return round(float(numerator) / denominator, 4) if denominator else 0.0


def analyze_campaign_metrics(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not rows:
        return {
            "totals": {"status": "no_metrics_provided"},
            "per_campaign": [],
            "insights": ["No campaign rows were provided."],
            "best_campaign": None,
            "worst_campaign": None,
        }

    df = pd.DataFrame(rows)
    for col in ["spend", "impressions", "clicks", "conversions", "revenue"]:
        if col not in df.columns:
            df[col] = 0
    if "campaign" not in df.columns:
        df["campaign"] = "default"

    grouped = df.groupby("campaign", as_index=False).sum(numeric_only=True)
    grouped["ctr_pct"] = grouped.apply(lambda r: round(_safe_rate(r["clicks"], r["impressions"]) * 100, 2), axis=1)
    grouped["cpc"] = grouped.apply(lambda r: round(_safe_rate(r["spend"], r["clicks"]), 2), axis=1)
    grouped["cpa"] = grouped.apply(lambda r: round(_safe_rate(r["spend"], r["conversions"]), 2), axis=1)
    grouped["roas"] = grouped.apply(lambda r: round(_safe_rate(r["revenue"], r["spend"]), 2), axis=1)

    total_spend = float(df["spend"].sum())
    total_revenue = float(df["revenue"].sum())
    totals = {
        "spend": round(total_spend, 2),
        "impressions": int(df["impressions"].sum()),
        "clicks": int(df["clicks"].sum()),
        "conversions": int(df["conversions"].sum()),
        "revenue": round(total_revenue, 2),
        "ctr_pct": round(_safe_rate(float(df["clicks"].sum()), float(df["impressions"].sum())) * 100, 2),
        "cpc": round(_safe_rate(total_spend, float(df["clicks"].sum())), 2),
        "cpa": round(_safe_rate(total_spend, float(df["conversions"].sum())), 2),
        "roas": round(_safe_rate(total_revenue, total_spend), 2),
    }

    ranked = grouped[grouped["conversions"] > 0].sort_values("roas", ascending=False)
    best = str(ranked.iloc[0]["campaign"]) if len(ranked) else None
    worst = str(ranked.iloc[-1]["campaign"]) if len(ranked) else None

    insights: List[str] = []
    if best:
        top = ranked.iloc[0]
        insights.append(f"Best ROAS: {best} at {top['roas']}x with CPA {top['cpa']}. Shift budget toward it first.")
    if worst and worst != best:
        low = ranked.iloc[-1]
        insights.append(f"Weakest ROAS: {worst} at {low['roas']}x with CPA {low['cpa']}. Review targeting and creative before adding spend.")
    if totals["ctr_pct"] and totals["ctr_pct"] < 1.0:
        insights.append("Overall CTR is below 1 percent. Creative and audience match need work before scaling.")
    if totals["roas"] and totals["roas"] >= 3.0:
        insights.append("Blended ROAS is at or above 3x. The funnel can absorb a controlled budget increase.")
    if not insights:
        insights.append("Metrics are within normal ranges. No strong signal to change budget yet.")

    return {
        "totals": totals,
        "per_campaign": grouped.to_dict(orient="records"),
        "insights": insights,
        "best_campaign": best,
        "worst_campaign": worst,
    }
