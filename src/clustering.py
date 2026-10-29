"""
KMeans Customer Segmentation and Cluster Interpretation Pipeline.

Performs:
- Skew-aware log1p feature transformation.
- Feature standardization via StandardScaler.
- Scikit-Learn KMeans clustering with fixed seed for strict reproducibility.
- Silhouette analysis and inertia calculation across candidate cluster counts.
- Dynamic data-driven semantic cluster labeling based on centroid metrics.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler


def preprocess_rfm_features(rfm_df: pd.DataFrame) -> Tuple[np.ndarray, StandardScaler]:
    """
    Apply log1p transformation to mitigate severe right skewness, followed by z-score standardization.
    """
    feature_cols = ["Recency", "Frequency", "Monetary"]
    data = rfm_df[feature_cols].copy()

    # Log1p transforms to stabilize high-variance financial distributions
    log_transformed = np.log1p(np.clip(data.values, a_min=0, a_max=None))

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(log_transformed)
    return scaled_features, scaler


def evaluate_cluster_range(
    scaled_features: np.ndarray,
    k_min: int = 2,
    k_max: int = 6,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    Compute Inertia and Silhouette scores across candidate k values.
    """
    n_samples = len(scaled_features)
    results = []

    k_max = min(k_max, n_samples - 1)
    if k_max < k_min:
        return pd.DataFrame(columns=["k", "inertia", "silhouette"])

    for k in range(k_min, k_max + 1):
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(scaled_features)
        inertia = float(km.inertia_)

        if n_samples > k and len(np.unique(labels)) > 1:
            sil = float(silhouette_score(scaled_features, labels))
        else:
            sil = 0.0

        results.append({"k": k, "inertia": round(inertia, 2), "silhouette": round(sil, 4)})

    return pd.DataFrame(results)


def interpret_and_label_clusters(cluster_summary: pd.DataFrame) -> Dict[int, str]:
    """
    Assign meaningful segment labels by evaluating relative centroid values of Recency, Frequency, and Monetary.
    
    Interpretive Rules:
    - Low Recency + High Frequency + High Monetary => "Champions / High-Value"
    - Moderate/Low Recency + High Frequency => "Loyal Customers"
    - Low Recency + Low/Moderate Frequency => "Recent / Potential Loyalists"
    - High Recency + High Frequency/Monetary => "At-Risk Customers"
    - High Recency + Low Frequency + Low Monetary => "Lost / Hibernating"
    """
    labels_map: Dict[int, str] = {}
    if cluster_summary.empty:
        return labels_map

    k = len(cluster_summary)
    df = cluster_summary.copy()

    # Ranks (1 is lowest, k is highest)
    # For Recency: lower is better (more recent)
    df["R_Rank"] = df["Mean_Recency"].rank(ascending=False) # higher rank = more recent (lower recency)
    df["F_Rank"] = df["Mean_Frequency"].rank(ascending=True) # higher rank = more frequent
    df["M_Rank"] = df["Mean_Monetary"].rank(ascending=True)  # higher rank = higher spend

    df["Overall_Score"] = df["R_Rank"] + df["F_Rank"] + df["M_Rank"]
    df = df.sort_values(by="Overall_Score", ascending=False)

    assigned_names: List[str] = []

    for _, row in df.iterrows():
        c_id = int(row["Cluster"])
        r_rec = row["Mean_Recency"]
        f_freq = row["Mean_Frequency"]
        m_spend = row["Mean_Monetary"]

        r_pct = row["R_Rank"] / k
        f_pct = row["F_Rank"] / k
        m_pct = row["M_Rank"] / k

        if m_pct >= 0.8 and f_pct >= 0.7 and "High-Value Champions" not in assigned_names:
            name = "High-Value Champions"
        elif f_pct >= 0.6 and r_pct >= 0.5 and "Loyal Customers" not in assigned_names:
            name = "Loyal Customers"
        elif r_pct >= 0.6 and f_pct <= 0.5 and "Recent / Promising" not in assigned_names:
            name = "Recent / Promising"
        elif r_pct <= 0.4 and (m_pct >= 0.5 or f_pct >= 0.5) and "At-Risk Customers" not in assigned_names:
            name = "At-Risk Customers"
        elif r_pct <= 0.3 and m_pct <= 0.4 and "Lost / Hibernating" not in assigned_names:
            name = "Lost / Hibernating"
        else:
            name = f"Segment {c_id + 1} (R:{int(r_rec)}d, F:{f_freq:.1f}, M:${int(m_spend)})"

        assigned_names.append(name)
        labels_map[c_id] = name

    return labels_map


def fit_kmeans_clustering(
    rfm_df: pd.DataFrame,
    n_clusters: int = 4,
    random_state: int = 42,
) -> Dict[str, Any]:
    """
    Full customer segmentation pipeline.
    
    Returns:
    - labeled_rfm: DataFrame with cluster IDs and descriptive segment names
    - cluster_summary: Metrics table by cluster
    - silhouette: Overall clustering silhouette score
    - evaluation_df: Elbow/silhouette progression
    """
    if len(rfm_df) < n_clusters:
        return {
            "status": "error",
            "message": f"Dataset has only {len(rfm_df)} customers, which is less than requested clusters ({n_clusters}).",
            "labeled_rfm": rfm_df.copy(),
            "cluster_summary": pd.DataFrame(),
            "silhouette": 0.0,
            "evaluation_df": pd.DataFrame(),
        }

    scaled_features, scaler = preprocess_rfm_features(rfm_df)
    eval_df = evaluate_cluster_range(scaled_features, k_min=2, k_max=max(6, n_clusters), random_state=random_state)

    kmeans = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    cluster_labels = kmeans.fit_predict(scaled_features)

    df_result = rfm_df.copy()
    df_result["Cluster"] = cluster_labels

    # Compute unscaled cluster metrics
    summary = df_result.groupby("Cluster").agg(
        CustomerCount=("CustomerID", "count"),
        Mean_Recency=("Recency", "mean"),
        Mean_Frequency=("Frequency", "mean"),
        Mean_Monetary=("Monetary", "mean"),
        Total_Monetary=("Monetary", "sum"),
    ).reset_index()

    total_revenue = summary["Total_Monetary"].sum()
    summary["RevenueSharePct"] = ((summary["Total_Monetary"] / total_revenue) * 100.0).round(2) if total_revenue > 0 else 0.0
    summary["Mean_Recency"] = summary["Mean_Recency"].round(1)
    summary["Mean_Frequency"] = summary["Mean_Frequency"].round(1)
    summary["Mean_Monetary"] = summary["Mean_Monetary"].round(2)

    # Dynamic semantic labeling
    labels_map = interpret_and_label_clusters(summary)
    df_result["Segment"] = df_result["Cluster"].map(labels_map)
    summary["Segment"] = summary["Cluster"].map(labels_map)

    # Reorder columns
    summary = summary[["Cluster", "Segment", "CustomerCount", "Mean_Recency", "Mean_Frequency", "Mean_Monetary", "RevenueSharePct"]]

    # Calculate overall silhouette
    sil = float(silhouette_score(scaled_features, cluster_labels)) if len(rfm_df) > n_clusters else 0.0

    return {
        "status": "success",
        "labeled_rfm": df_result,
        "cluster_summary": summary,
        "silhouette": round(sil, 4),
        "evaluation_df": eval_df,
        "kmeans_model": kmeans,
        "scaler": scaler,
    }
