from __future__ import annotations
from fastapi import APIRouter
import backend.data_service as ds
from src.product_recommendations import compute_association_rules

router = APIRouter()

@router.get("")
def get_recommendations(min_support: float = 0.01, min_confidence: float = 0.1, top_n: int = 30):
    df = ds.get_df()
    rules_df = compute_association_rules(
        df,
        basket_col="InvoiceNo",
        item_col="Description",
        min_support=min_support,
        min_confidence=min_confidence,
    )

    if rules_df.empty:
        return {"rules": []}

    rules = []
    for _, row in rules_df.head(top_n).iterrows():
        rules.append({
            "antecedents": str(row.get("Antecedent", "")),
            "consequents": str(row.get("Consequent", "")),
            "support": round(float(row.get("Support", 0)), 4),
            "confidence": round(float(row.get("Confidence", 0)), 4),
            "lift": round(float(row.get("Lift", 0)), 2),
        })

    return {"rules": rules}
