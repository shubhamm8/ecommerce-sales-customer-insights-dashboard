"""
Unit tests for association rule recommendations, business insights generator, and local AI assistant.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch
import pandas as pd
import pytest
from src.ai_assistant import ask_sales_assistant, build_analytical_context
from src.product_recommendations import compute_association_rules, get_product_recommendations
from src.recommendations import generate_business_insights


@pytest.fixture
def basket_transactions():
    # 20 invoices with deliberate co-occurrences of Item A and Item B
    rows = []
    for i in range(1, 21):
        inv = f"INV_{i}"
        # Everyone buys A and B together
        rows.append({"InvoiceNo": inv, "Description": "Coffee Mug", "Quantity": 1, "UnitPrice": 5.0, "NetRevenue": 5.0})
        rows.append({"InvoiceNo": inv, "Description": "Coffee Beans", "Quantity": 1, "UnitPrice": 12.0, "NetRevenue": 12.0})
        if i % 3 == 0:
            rows.append({"InvoiceNo": inv, "Description": "Teaspoon Set", "Quantity": 1, "UnitPrice": 3.0, "NetRevenue": 3.0})
    df = pd.DataFrame(rows)
    df["InvoiceDate"] = pd.to_datetime("2023-01-01")
    df["CustomerID"] = "101"
    df["Country"] = "United Kingdom"
    return df


def test_compute_association_rules(basket_transactions):
    rules = compute_association_rules(
        basket_transactions,
        basket_col="InvoiceNo",
        item_col="Description",
        min_support=0.1,
        min_confidence=0.5,
    )
    assert not rules.empty
    assert "Antecedent" in rules.columns
    assert "Consequent" in rules.columns
    assert "Lift" in rules.columns

    # Since Mug and Beans are in 100% of baskets, Confidence should be 1.0 and Lift should be 1.0
    mug_beans = rules[(rules["Antecedent"] == "Coffee Mug") & (rules["Consequent"] == "Coffee Beans")]
    assert len(mug_beans) == 1
    assert mug_beans.iloc[0]["Confidence"] == 1.0
    assert mug_beans.iloc[0]["Support"] == 1.0


def test_get_product_recommendations(basket_transactions):
    rules = compute_association_rules(
        basket_transactions,
        basket_col="InvoiceNo",
        item_col="Description",
        min_support=0.1,
        min_confidence=0.5,
    )
    recs = get_product_recommendations("Coffee Mug", rules, top_n=2)
    assert not recs.empty
    assert "RecommendedProduct" in recs.columns
    assert "Coffee Beans" in recs["RecommendedProduct"].values


def test_generate_business_insights(basket_transactions):
    insights = generate_business_insights(basket_transactions)
    assert len(insights) >= 1
    for ins in insights:
        assert "category" in ins
        assert "title" in ins
        assert "supporting_metric" in ins
        assert "why_it_matters" in ins
        assert "recommended_action" in ins
        assert "confidence" in ins


def test_ai_assistant_deterministic_fallback(basket_transactions):
    context = build_analytical_context(basket_transactions)
    # Test Revenue query
    res_rev = ask_sales_assistant("What is the total revenue?", context=context, use_local_llm=False)
    assert res_rev["mode"] == "deterministic"
    assert "Net Revenue:" in res_rev["answer"]

    # Test Product query
    res_prod = ask_sales_assistant("Which products sold the most?", context=context, use_local_llm=False)
    assert res_prod["mode"] == "deterministic"
    assert "Coffee" in res_prod["answer"]


@patch("src.local_llm.requests.post")
@patch("src.local_llm.requests.get")
def test_ai_assistant_mock_local_llm(mock_get, mock_post, basket_transactions):
    # Mock Ollama status call: daemon is online and has llama3.2:1b
    mock_get.return_value = MagicMock(status_code=200, json=lambda: {"models": [{"name": "llama3.2:1b"}]})
    # Mock Ollama generate call
    mock_post.return_value = MagicMock(
        status_code=200,
        json=lambda: {"response": "Mocked local LLM analysis: Total revenue is performing solidly."}
    )

    context = build_analytical_context(basket_transactions)
    res = ask_sales_assistant(
        "Summarize revenue",
        context=context,
        use_local_llm=True,
        selected_model="llama3.2:1b",
    )
    assert "LLM" in res["mode"]
    assert "Mocked local LLM analysis" in res["answer"]
