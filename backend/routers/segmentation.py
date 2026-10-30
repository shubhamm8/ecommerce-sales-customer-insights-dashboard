from __future__ import annotations
from fastapi import APIRouter, Query
import backend.data_service as ds
from src.rfm_analysis import compute_rfm_table
from src.clustering import fit_kmeans_clustering

router = APIRouter()

@router.get("")
def get_segmentation(k: int = Query(4, ge=2, le=10)):
    df = ds.get_df()
    rfm_df = compute_rfm_table(df)
    if len(rfm_df) < k:
        return {"rfm_labeled": [], "cluster_profiles": []}

    res = fit_kmeans_clustering(rfm_df, n_clusters=k)
    if res.get("status") == "error":
        return {"rfm_labeled": [], "cluster_profiles": []}

    labeled = res["labeled_rfm"]
    summary = res["cluster_summary"]

    profiles = []
    for _, row in summary.iterrows():
        profiles.append({
            "Cluster": int(row["Cluster"]),
            "CustomerCount": int(row["CustomerCount"]),
            "AvgRevenue": round(float(row["Mean_Monetary"]), 2),
            "AvgRFMScore": round(float(row.get("Mean_Frequency", 0)), 1),
            "RevenueSharePct": round(float(row.get("RevenueSharePct", 0)), 1),
        })

    labeled_records = labeled[["CustomerID", "Recency", "Frequency", "Monetary", "Cluster"]].to_dict(orient="records")

    return {
        "rfm_labeled": labeled_records,
        "cluster_profiles": profiles,
        "silhouette": res.get("silhouette", 0.0),
    }
