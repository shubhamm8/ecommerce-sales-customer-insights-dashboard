"""
Dual-Engine AI Sales and Business Intelligence Assistant.

Architecture:
1. Analytical Context Builder: Pre-aggregates privacy-safe KPIs (zero raw PII).
2. Intent Classifier & Tool Router: Maps queries to exact verified analytical calculations.
3. Local Generative LLM Mode (via Ollama): Synthesizes conversational responses strictly grounded in evidence.
4. Deterministic Rule-Based Fallback: Provides reliable, verifiable query responses when Ollama is offline.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from src.local_llm import check_ollama_status, generate_local_response
from src.metrics import compute_executive_kpis, compute_period_over_period
from src.sales_analysis import analyze_geographic_sales, analyze_product_performance


def build_analytical_context(
    df: pd.DataFrame,
    rfm_labeled_df: Optional[pd.DataFrame] = None,
    forecast_results: Optional[Dict[str, Any]] = None,
    anomaly_results: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Assemble aggregated, privacy-conscious business metrics into a structured analytical context.
    """
    if df.empty:
        return {"status": "empty_dataset"}

    kpis = compute_executive_kpis(df)
    pop = compute_period_over_period(df)
    prod = analyze_product_performance(df, top_n=5)
    geo = analyze_geographic_sales(df, top_n=5)

    context = {
        "status": "ready",
        "kpis": kpis,
        "period_change": pop,
        "top_products": prod["top_revenue"].to_dict(orient="records"),
        "top_countries": geo.to_dict(orient="records"),
        "has_rfm": False,
        "segments": [],
        "has_forecast": False,
        "forecast_metrics": None,
        "has_anomalies": False,
        "anomaly_count": 0,
    }

    if rfm_labeled_df is not None and not rfm_labeled_df.empty and "Segment" in rfm_labeled_df.columns:
        seg_summary = rfm_labeled_df.groupby("Segment").agg(
            Count=("CustomerID", "count"),
            Revenue=("Monetary", "sum"),
            AvgSpend=("Monetary", "mean"),
            AvgRecency=("Recency", "mean"),
        ).reset_index()
        context["has_rfm"] = True
        context["segments"] = seg_summary.to_dict(orient="records")

    if forecast_results and forecast_results.get("status") == "success":
        context["has_forecast"] = True
        context["forecast_metrics"] = forecast_results.get("metrics_model")

    if anomaly_results and anomaly_results.get("status") == "success":
        context["has_anomalies"] = True
        context["anomaly_count"] = anomaly_results.get("anomaly_count", 0)

    return context


def answer_with_deterministic_assistant(query: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic rule-based query responder. Transparently computes and formats answers directly from context.
    """
    q = query.lower()
    kpis = context.get("kpis", {})

    # Intent 1: Revenue & Financials
    if any(k in q for k in ["revenue", "sales", "gross", "net", "total make", "earnings", "refund"]):
        net_rev = kpis.get("total_net_revenue", 0.0)
        gross_rev = kpis.get("total_gross_revenue", 0.0)
        refunds = kpis.get("total_refunds", 0.0)
        aov = kpis.get("average_order_value", 0.0)

        response_text = (
            f"### Verified Financial Summary\n\n"
            f"- **Net Revenue:** ${net_rev:,.2f}\n"
            f"- **Gross Revenue:** ${gross_rev:,.2f}\n"
            f"- **Total Refunds / Returns:** ${refunds:,.2f}\n"
            f"- **Average Order Value (AOV):** ${aov:,.2f}\n\n"
            f"*Evidence: Computed from {kpis.get('total_orders', 0):,} verified completed invoices.*"
        )
        return {
            "mode": "deterministic",
            "intent": "revenue_summary",
            "answer": response_text,
            "evidence": {"NetRevenue": net_rev, "GrossRevenue": gross_rev, "AOV": aov},
        }

    # Intent 2: Top Products
    if any(k in q for k in ["product", "item", "sku", "best seller", "top sell"]):
        top_prods = context.get("top_products", [])
        if not top_prods:
            return {"mode": "deterministic", "intent": "products", "answer": "No product data available in active dataset."}

        lines = ["### Top Products by Net Revenue\n"]
        for idx, p in enumerate(top_prods, 1):
            lines.append(f"{idx}. **{p.get('Description')}** — ${p.get('Revenue', 0):,.2f} ({p.get('UnitsSold', 0):,} units sold)")

        lines.append(f"\n*Evidence: Aggregate sales across all non-refund order lines.*")
        return {
            "mode": "deterministic",
            "intent": "product_ranking",
            "answer": "\n".join(lines),
            "evidence": top_prods,
        }

    # Intent 3: Geographic / Countries
    if any(k in q for k in ["country", "region", "international", "where", "location", "geography"]):
        top_countries = context.get("top_countries", [])
        if not top_countries:
            return {"mode": "deterministic", "intent": "geography", "answer": "No geographic data available in dataset."}

        lines = ["### Top Revenue Contributing Countries\n"]
        for idx, c in enumerate(top_countries, 1):
            lines.append(f"{idx}. **{c.get('Country')}** — ${c.get('Revenue', 0):,.2f} ({c.get('RevenueSharePct', 0)}% of global sales)")

        return {
            "mode": "deterministic",
            "intent": "geographic_ranking",
            "answer": "\n".join(lines),
            "evidence": top_countries,
        }

    # Intent 4: Customer Segmentation / RFM
    if any(k in q for k in ["segment", "customer", "rfm", "loyal", "champion", "at-risk", "churn"]):
        segments = context.get("segments", [])
        if not segments:
            return {
                "mode": "deterministic",
                "intent": "customer_segments",
                "answer": f"The dataset contains **{kpis.get('unique_customers', 0):,} unique customers** with a repeat customer rate of **{kpis.get('repeat_customer_rate', 0)}%**. To view detailed KMeans cluster segments, visit the Customer Segmentation page.",
            }

        lines = ["### Customer Segment Distribution (KMeans RFM)\n"]
        for s in segments:
            lines.append(
                f"- **{s.get('Segment')}**: {s.get('Count', 0)} customers, Total Spend: ${s.get('Revenue', 0):,.2f} (Avg Recency: {s.get('AvgRecency', 0):.0f} days)"
            )
        return {
            "mode": "deterministic",
            "intent": "customer_segments",
            "answer": "\n".join(lines),
            "evidence": segments,
        }

    # Intent 5: Period over Period / Growth / Trends
    if any(k in q for k in ["growth", "trend", "change", "period", "momentum", "compare", "month"]):
        pop = context.get("period_change", {})
        if pop.get("status") == "valid":
            delta = pop.get("delta_pct", 0)
            sign = "+" if delta >= 0 else ""
            ans = (
                f"### Period-over-Period Performance Shift\n\n"
                f"- **Growth Rate:** **{sign}{delta:.1f}%**\n"
                f"- **Current Period Revenue:** ${pop.get('current_value', 0):,.2f}\n"
                f"- **Previous Period Revenue:** ${pop.get('previous_value', 0):,.2f}\n"
                f"- **Comparison Midpoint:** {pop.get('period_midpoint')}\n\n"
                f"Sales velocity is {'accelerating' if delta >= 0 else 'contracting'} relative to the prior baseline period."
            )
            return {"mode": "deterministic", "intent": "trend_analysis", "answer": ans, "evidence": pop}

    # Default overview synthesis
    net_rev = kpis.get("total_net_revenue", 0.0)
    orders = kpis.get("total_orders", 0)
    custs = kpis.get("unique_customers", 0)
    top_p = context.get("top_products", [{}])[0].get("Description", "N/A")

    default_ans = (
        f"### Executive Analytical Briefing\n\n"
        f"Based on the active dataset calculations:\n"
        f"- **Total Net Revenue:** ${net_rev:,.2f} across **{orders:,} orders**\n"
        f"- **Identified Customers:** {custs:,} buyers (Repeat Rate: {kpis.get('repeat_customer_rate', 0)}%)\n"
        f"- **Leading SKU:** {top_p}\n"
        f"- **Cancellation / Refund Rate:** {kpis.get('cancellation_rate', 0)}%\n\n"
        f"You can ask specific questions about revenue, top products, customer segments, trends, or anomaly findings."
    )
    return {"mode": "deterministic", "intent": "general_overview", "answer": default_ans, "evidence": kpis}


def ask_sales_assistant(
    query: str,
    context: Dict[str, Any],
    use_local_llm: bool = False,
    selected_model: str = "llama3.2:1b",
    host: str = "http://127.0.0.1:11434",
) -> Dict[str, Any]:
    """
    Main Assistant Entrypoint.
    If local LLM is requested and active, uses Ollama; otherwise executes deterministic rules.
    """
    if context.get("status") == "empty_dataset":
        return {
            "mode": "system",
            "answer": "No dataset loaded yet. Please upload a dataset or load the sample e-commerce data to interact with the assistant.",
            "evidence": None,
        }

    # Check if local generative LLM is enabled and online
    if use_local_llm:
        status = check_ollama_status(host=host)
        if status.get("available") and selected_model in status.get("models", []):
            system_prompt = (
                "You are an expert AI E-Commerce Sales Analyst. You have been provided with "
                "verified aggregated metrics from the company's real transaction dataset.\n"
                "STRICT RULES:\n"
                "1. Answer strictly using ONLY the supplied numerical context.\n"
                "2. NEVER invent numbers, revenue figures, or customer statistics.\n"
                "3. If information is not provided in the context, explicitly state that it is not available in the dataset.\n"
                "4. Be professional, concise, and highlight actionable business implications.\n"
            )

            prompt = (
                f"Context Data:\n{context}\n\n"
                f"User Question: {query}\n\n"
                f"Please provide an accurate, data-grounded response."
            )

            llm_result = generate_local_response(
                prompt=prompt,
                system_prompt=system_prompt,
                model=selected_model,
                host=host,
            )

            if llm_result.get("success"):
                return {
                    "mode": f"Local LLM ({selected_model})",
                    "answer": llm_result.get("response"),
                    "evidence": context.get("kpis"),
                }

    # Fallback to deterministic engine
    fallback_res = answer_with_deterministic_assistant(query, context)
    return fallback_res
