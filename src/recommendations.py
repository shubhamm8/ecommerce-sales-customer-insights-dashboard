"""
Automated Business Insights and Strategic Recommendations Engine.

Derives evidence-backed insights across 7 business dimensions:
1. Top Revenue Driver Products
2. Revenue Concentration (Pareto Risk)
3. Customer Segment Opportunities (Champions vs At-Risk)
4. Period-over-Period Performance Shift
5. Geographic Distribution Opportunities
6. Return/Refund Leakage Risk
7. Anomaly and Operational Fluctuations
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd
from src.metrics import compute_executive_kpis, compute_period_over_period
from src.sales_analysis import analyze_geographic_sales, analyze_product_performance


def generate_business_insights(
    df: pd.DataFrame,
    rfm_labeled_df: Optional[pd.DataFrame] = None,
    anomaly_summary: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Run deterministic diagnostic rules over actual dataset metrics to produce strategic business findings.
    """
    insights: List[Dict[str, Any]] = []
    if df.empty:
        return insights

    kpis = compute_executive_kpis(df)
    pop = compute_period_over_period(df)
    prod_perf = analyze_product_performance(df, top_n=5)
    geo_perf = analyze_geographic_sales(df, top_n=5)

    # 1. Period-over-Period Revenue Momentum
    if pop["status"] == "valid":
        delta = pop["delta_pct"]
        if delta >= 0:
            direction = "Growth"
            action = "Maintain promotional momentum, ensure inventory replenishment for high-velocity SKUs, and expand ad-spend on top performing regions."
            tag = "Positive Trend"
        else:
            direction = "Decline"
            action = "Audit recent pricing changes, test targeted win-back email campaigns, and inspect checkout drop-off rates."
            tag = "Attention Required"

        insights.append({
            "category": "Revenue Trajectory",
            "tag": tag,
            "title": f"Recent Period Sales Shift: {delta:+.1f}% {direction}",
            "supporting_metric": f"Current Period Revenue: ${pop['current_value']:,.2f} vs Previous: ${pop['previous_value']:,.2f}",
            "comparison": f"Evaluated across midpoint {pop['period_midpoint']}",
            "why_it_matters": "Understanding period momentum highlights whether commercial velocity is accelerating or encountering headwinds before quarterly closes.",
            "recommended_action": action,
            "confidence": "High (Direct Historical Aggregation)",
        })

    # 2. Top Product Revenue Driver
    top_prods = prod_perf["top_revenue"]
    if not top_prods.empty:
        star_product = top_prods.iloc[0]["Description"]
        star_rev = float(top_prods.iloc[0]["Revenue"])
        total_rev = kpis["total_net_revenue"]
        share = (star_rev / total_rev * 100.0) if total_rev > 0 else 0.0

        insights.append({
            "category": "Product Strategy",
            "tag": "Key Revenue Driver",
            "title": f"Flagship SKU: '{star_product}'",
            "supporting_metric": f"${star_rev:,.2f} generated ({share:.1f}% of total net sales)",
            "comparison": "Relative to all catalog items",
            "why_it_matters": "A single flagship product driving significant share represents both a core cash generator and an inventory dependency risk.",
            "recommended_action": f"Prioritize supplier safety stock for '{star_product}' to avoid stockouts, and bundle it with complementary slower-moving accessories.",
            "confidence": "High (Catalog Transaction Ranking)",
        })

    # 3. Product Portfolio Concentration Risk
    if len(top_prods) >= 3:
        top_3_rev = float(top_prods.head(3)["Revenue"].sum())
        top_3_share = (top_3_rev / kpis["total_net_revenue"] * 100.0) if kpis["total_net_revenue"] > 0 else 0.0
        if top_3_share > 30.0:
            insights.append({
                "category": "Risk Management",
                "tag": "Concentration Risk",
                "title": f"Catalog Concentration: Top 3 SKUs Drive {top_3_share:.1f}% of Revenue",
                "supporting_metric": f"${top_3_rev:,.2f} across top 3 products out of {kpis['total_skus']} total catalog SKUs",
                "comparison": "Top 3 Products vs Entire Catalog",
                "why_it_matters": "Heavy revenue reliance on very few SKUs makes the business vulnerable to supplier disruptions or competitive substitute products.",
                "recommended_action": "Diversify marketing budget toward mid-tier products with high margins to build a resilient, balanced product portfolio.",
                "confidence": "High (Empirical Concentration)",
            })

    # 4. Customer Segmentation Insights (Champions vs At-Risk)
    if rfm_labeled_df is not None and not rfm_labeled_df.empty and "Segment" in rfm_labeled_df.columns:
        seg_summary = rfm_labeled_df.groupby("Segment").agg(
            Count=("CustomerID", "count"),
            Revenue=("Monetary", "sum"),
            AvgRecency=("Recency", "mean"),
        ).reset_index()

        total_seg_rev = seg_summary["Revenue"].sum()

        for _, s_row in seg_summary.iterrows():
            seg_name = s_row["Segment"]
            c_cnt = int(s_row["Count"])
            s_rev = float(s_row["Revenue"])
            s_share = (s_rev / total_seg_rev * 100.0) if total_seg_rev > 0 else 0.0

            if "Champion" in seg_name or "High-Value" in seg_name:
                insights.append({
                    "category": "Customer Retention",
                    "tag": "High-Value Segment",
                    "title": f"{seg_name}: {c_cnt} VIP Clients Driving {s_share:.1f}% Revenue",
                    "supporting_metric": f"${s_rev:,.2f} total spend (Avg recency: {s_row['AvgRecency']:.0f} days)",
                    "comparison": f"{c_cnt} VIPs vs {len(rfm_labeled_df)} total customer cohort",
                    "why_it_matters": "High-value champions have the highest customer lifetime value and are the primary source of organic customer advocacy.",
                    "recommended_action": "Enroll this segment into an exclusive VIP loyalty tier, offer early access to new releases, and assign dedicated customer support.",
                    "confidence": "High (KMeans RFM Cluster)",
                })
            elif "At-Risk" in seg_name:
                insights.append({
                    "category": "Customer Retention",
                    "tag": "Retention Urgency",
                    "title": f"{seg_name}: {c_cnt} Customers at Imminent Risk of Churn",
                    "supporting_metric": f"${s_rev:,.2f} historical value; dormant for an average of {s_row['AvgRecency']:.0f} days",
                    "comparison": "Previously active multi-order buyers now disengaged",
                    "why_it_matters": "Re-activating existing customers costs significantly less than acquiring new cold traffic.",
                    "recommended_action": "Trigger an automated re-engagement campaign offering personalized discounts based on their past purchase categories.",
                    "confidence": "High (RFM Recency Decay)",
                })

    # 5. Geographic Expansion Opportunity
    if not geo_perf.empty and len(geo_perf) > 1:
        primary_country = geo_perf.iloc[0]["Country"]
        primary_share = geo_perf.iloc[0]["RevenueSharePct"]
        second_country = geo_perf.iloc[1]["Country"]
        second_rev = geo_perf.iloc[1]["Revenue"]
        second_share = geo_perf.iloc[1]["RevenueSharePct"]

        insights.append({
            "category": "Geographic Expansion",
            "tag": "International Growth",
            "title": f"Secondary Market Potential in {second_country}",
            "supporting_metric": f"${second_rev:,.2f} ({second_share:.1f}% share) vs Primary {primary_country} ({primary_share:.1f}%)",
            "comparison": f"Top international market after {primary_country}",
            "why_it_matters": "Demonstrated organic cross-border demand indicates an opportunity for market penetration without speculative expansion risk.",
            "recommended_action": f"Localize currency and shipping options for {second_country} and partner with localized logistics providers to reduce transit times.",
            "confidence": "Medium-High (Cross-Border Sales Distribution)",
        })

    # 6. Cancellation & Refund Leakage
    if kpis["cancellation_rate"] > 3.0 or kpis["total_refunds"] > 0:
        c_rate = kpis["cancellation_rate"]
        ref_amt = kpis["total_refunds"]
        insights.append({
            "category": "Operational Efficiency",
            "tag": "Margin Protection",
            "title": f"Return & Refund Exposure: ${ref_amt:,.2f} ({c_rate:.1f}% Invoice Cancellation Rate)",
            "supporting_metric": f"${ref_amt:,.2f} returned across {c_rate:.1f}% of order volume",
            "comparison": "Net impact on gross commercial margin",
            "why_it_matters": "Excessive refunds increase reverse logistics costs, damage customer trust, and distort inventory tracking.",
            "recommended_action": "Audit top returned SKUs for quality or size description mismatches and improve packaging durability for fragile items.",
            "confidence": "High (Recorded Returns Flagging)",
        })

    # 7. Operational Anomaly Summary
    if anomaly_summary and anomaly_summary.get("status") == "success":
        anom_cnt = anomaly_summary.get("anomaly_count", 0)
        if anom_cnt > 0:
            insights.append({
                "category": "Operational Monitoring",
                "tag": "Statistical Anomalies",
                "title": f"{anom_cnt} Potential Sales Anomalies Detected",
                "supporting_metric": f"{anom_cnt} date points ({anomaly_summary.get('anomaly_rate', 0):.1f}% of timeline) flagged by {anomaly_summary.get('method')}",
                "comparison": "Against normal baseline confidence bounds",
                "why_it_matters": "Unexplained sales spikes or sudden dips often pinpoint stockouts, marketing campaign launches, or platform technical glitches.",
                "recommended_action": "Correlate identified outlier dates against marketing campaigns and inventory logs to isolate root causes.",
                "confidence": "Medium (Statistical Anomaly Detection)",
            })

    return insights
