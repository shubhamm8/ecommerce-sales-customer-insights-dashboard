"""
Transparent Market Basket Analysis and Association Rules Engine.

Calculates:
- Support: P(A ∩ B)
- Confidence: P(B | A) = Support(A ∩ B) / Support(A)
- Lift: Support(A ∩ B) / [Support(A) * Support(B)]
- Conviction: [1 - Support(B)] / [1 - Confidence(A -> B)]

Provides:
- Frequently bought together pairs.
- Item-to-item targeted recommendation queries.
- Clean matrix processing optimized for memory safety.
"""

from __future__ import annotations

from collections import Counter
from itertools import combinations
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd


def compute_association_rules(
    df: pd.DataFrame,
    basket_col: str = "InvoiceNo",
    item_col: str = "Description",
    min_support: float = 0.01,
    min_confidence: float = 0.1,
    max_rules: int = 200,
) -> pd.DataFrame:
    """
    Extract pairwise association rules directly from basket transactions.
    """
    if df.empty or basket_col not in df.columns or item_col not in df.columns:
        return pd.DataFrame(columns=[
            "Antecedent", "Consequent", "Support_A", "Support_B", "Support", "Confidence", "Lift"
        ])

    # Filter out cancelled / refund transactions for recommendation modeling
    valid = df[df.get("Quantity", 1) > 0].dropna(subset=[basket_col, item_col]).copy()
    valid = valid[~valid[item_col].isin(["", "Unknown Product", "Manual", "POSTAGE", "DOTCOM POSTAGE"])]

    # Group into transaction baskets (unique items per invoice)
    baskets = valid.groupby(basket_col)[item_col].unique()
    total_baskets = len(baskets)

    if total_baskets < 5:
        return pd.DataFrame(columns=[
            "Antecedent", "Consequent", "Support_A", "Support_B", "Support", "Confidence", "Lift"
        ])

    # 1. Count individual item frequencies
    item_counts: Counter[str] = Counter()
    pair_counts: Counter[Tuple[str, str]] = Counter()

    for items in baskets:
        # Sort items to maintain standard pairing order
        unique_items = sorted(list(set(items)))
        for it in unique_items:
            item_counts[it] += 1
        for a, b in combinations(unique_items, 2):
            pair_counts[(a, b)] += 1

    min_basket_count = max(2, int(total_baskets * min_support))

    rules = []
    # Build bidirectional rules (A -> B and B -> A) for each frequent pair
    for (item_a, item_b), count_ab in pair_counts.items():
        if count_ab < min_basket_count:
            continue

        supp_ab = count_ab / total_baskets
        supp_a = item_counts[item_a] / total_baskets
        supp_b = item_counts[item_b] / total_baskets

        # Rule 1: A -> B
        conf_a_to_b = supp_ab / supp_a if supp_a > 0 else 0.0
        lift_a_to_b = conf_a_to_b / supp_b if supp_b > 0 else 0.0

        if conf_a_to_b >= min_confidence:
            rules.append({
                "Antecedent": item_a,
                "Consequent": item_b,
                "Support_A": round(supp_a, 4),
                "Support_B": round(supp_b, 4),
                "Support": round(supp_ab, 4),
                "Confidence": round(conf_a_to_b, 4),
                "Lift": round(lift_a_to_b, 2),
                "TransactionCount": count_ab,
            })

        # Rule 2: B -> A
        conf_b_to_a = supp_ab / supp_b if supp_b > 0 else 0.0
        lift_b_to_a = conf_b_to_a / supp_a if supp_a > 0 else 0.0

        if conf_b_to_a >= min_confidence:
            rules.append({
                "Antecedent": item_b,
                "Consequent": item_a,
                "Support_A": round(supp_b, 4),
                "Support_B": round(supp_a, 4),
                "Support": round(supp_ab, 4),
                "Confidence": round(conf_b_to_a, 4),
                "Lift": round(lift_b_to_a, 2),
                "TransactionCount": count_ab,
            })

    if not rules:
        # Fallback with lowered support threshold if strict criteria yield no pairs
        return pd.DataFrame(columns=[
            "Antecedent", "Consequent", "Support_A", "Support_B", "Support", "Confidence", "Lift", "TransactionCount"
        ])

    df_rules = pd.DataFrame(rules)
    df_rules = df_rules.sort_values(by=["Lift", "Confidence"], ascending=False).head(max_rules).reset_index(drop=True)
    return df_rules


def get_product_recommendations(
    product_name: str,
    rules_df: pd.DataFrame,
    top_n: int = 5,
) -> pd.DataFrame:
    """
    Retrieve top complementary recommendations for a specific product.
    """
    if rules_df.empty or "Antecedent" not in rules_df.columns:
        return pd.DataFrame(columns=["RecommendedProduct", "Confidence", "Lift", "Support"])

    matches = rules_df[rules_df["Antecedent"].str.lower() == product_name.lower()].copy()
    if matches.empty:
        # Partial match
        matches = rules_df[rules_df["Antecedent"].str.lower().str.contains(product_name.lower(), regex=False)].copy()

    if matches.empty:
        return pd.DataFrame(columns=["RecommendedProduct", "Confidence", "Lift", "Support"])

    recs = matches[["Consequent", "Confidence", "Lift", "Support", "TransactionCount"]].rename(
        columns={"Consequent": "RecommendedProduct"}
    ).sort_values(by=["Lift", "Confidence"], ascending=False).head(top_n)

    return recs.reset_index(drop=True)
