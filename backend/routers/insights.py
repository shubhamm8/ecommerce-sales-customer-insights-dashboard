from __future__ import annotations
from fastapi import APIRouter
import backend.data_service as ds
from src.recommendations import generate_business_insights
from src.rfm_analysis import compute_rfm_table
from src.clustering import fit_kmeans_clustering

router = APIRouter()

@router.get("")
def get_insights():
    df = ds.get_df()
    rfm_labeled = None
    if "CustomerID" in df.columns and not df["CustomerID"].dropna().empty:
        rfm_table = compute_rfm_table(df)
        if len(rfm_table) >= 4:
            km_res = fit_kmeans_clustering(rfm_table, n_clusters=4)
            if km_res.get("status") == "success":
                rfm_labeled = km_res["labeled_rfm"]
    
    insights = generate_business_insights(df, rfm_labeled_df=rfm_labeled)
    return {"insights": insights}
