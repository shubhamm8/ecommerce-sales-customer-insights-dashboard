"""
Unit tests for KMeans clustering and dynamic segment labeling.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.clustering import evaluate_cluster_range, fit_kmeans_clustering, preprocess_rfm_features


@pytest.fixture
def synthetic_rfm_population():
    rng = np.random.default_rng(42)
    n = 60
    # Create 3 distinct customer behavioral patterns:
    # 1. VIP Champions: low recency, high frequency, high spend
    c_champ = pd.DataFrame({
        "CustomerID": [f"CHAMP_{i}" for i in range(20)],
        "Recency": rng.integers(1, 15, size=20),
        "Frequency": rng.integers(10, 25, size=20),
        "Monetary": rng.uniform(1500, 4000, size=20),
    })
    # 2. Loyal Mid-tier: moderate recency, moderate frequency, moderate spend
    c_loyal = pd.DataFrame({
        "CustomerID": [f"LOYAL_{i}" for i in range(20)],
        "Recency": rng.integers(15, 60, size=20),
        "Frequency": rng.integers(4, 9, size=20),
        "Monetary": rng.uniform(400, 1200, size=20),
    })
    # 3. At-risk / One-time: high recency, 1 order, low spend
    c_churn = pd.DataFrame({
        "CustomerID": [f"CHURN_{i}" for i in range(20)],
        "Recency": rng.integers(150, 300, size=20),
        "Frequency": rng.integers(1, 2, size=20),
        "Monetary": rng.uniform(20, 150, size=20),
    })
    return pd.concat([c_champ, c_loyal, c_churn], ignore_index=True)


def test_preprocess_rfm_features(synthetic_rfm_population):
    scaled, scaler = preprocess_rfm_features(synthetic_rfm_population)
    assert scaled.shape == (60, 3)
    # StandardScaler guarantees approximately 0 mean and 1 variance
    assert np.allclose(np.mean(scaled, axis=0), 0.0, atol=1e-2)
    assert np.allclose(np.std(scaled, axis=0), 1.0, atol=1e-2)


def test_evaluate_cluster_range(synthetic_rfm_population):
    scaled, _ = preprocess_rfm_features(synthetic_rfm_population)
    eval_df = evaluate_cluster_range(scaled, k_min=2, k_max=4, random_state=42)
    assert len(eval_df) == 3
    assert "k" in eval_df.columns
    assert "inertia" in eval_df.columns
    assert "silhouette" in eval_df.columns
    # Silhouette score should be healthy (> 0.3)
    assert eval_df["silhouette"].max() > 0.3


def test_fit_kmeans_clustering_reproducibility(synthetic_rfm_population):
    res1 = fit_kmeans_clustering(synthetic_rfm_population, n_clusters=3, random_state=42)
    res2 = fit_kmeans_clustering(synthetic_rfm_population, n_clusters=3, random_state=42)

    assert res1["status"] == "success"
    # Strict determinism test
    assert np.array_equal(res1["labeled_rfm"]["Cluster"].values, res2["labeled_rfm"]["Cluster"].values)
    assert "Segment" in res1["labeled_rfm"].columns
    assert len(res1["cluster_summary"]) == 3


def test_fit_kmeans_small_population():
    tiny_rfm = pd.DataFrame({
        "CustomerID": ["1", "2"],
        "Recency": [5, 10],
        "Frequency": [1, 2],
        "Monetary": [50.0, 100.0],
    })
    # Requesting 4 clusters with only 2 customers should yield graceful error status
    res = fit_kmeans_clustering(tiny_rfm, n_clusters=4)
    assert res["status"] == "error"
