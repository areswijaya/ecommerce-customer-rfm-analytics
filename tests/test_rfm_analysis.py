"""
Unit tests for RFM Analysis module.
Follows Arrange-Act-Assert (AAA) pattern.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np

from rfm_analysis import (
    compute_rfm_metrics,
    score_and_segment_rfm,
    generate_rfm_summary,
)


@pytest.fixture
def sample_data():
    """
    Arrange fixture data with controlled orders, customers, and order items.
    Customer 1 has 2 delivered orders on different dates with distinct customer_ids.
    Customer 2 has 1 delivered order.
    Customer 3 has 1 canceled order (must be filtered out).
    """
    orders_df = pd.DataFrame({
        "order_id": ["ord_1", "ord_2", "ord_3", "ord_4"],
        "customer_id": ["cust_a1", "cust_a2", "cust_b1", "cust_c1"],
        "order_status": ["delivered", "delivered", "delivered", "canceled"],
        "order_purchase_timestamp": [
            "2018-08-01 10:00:00",
            "2018-08-20 10:00:00",
            "2018-07-15 10:00:00",
            "2018-08-25 10:00:00",
        ]
    })

    customers_df = pd.DataFrame({
        "customer_id": ["cust_a1", "cust_a2", "cust_b1", "cust_c1"],
        "customer_unique_id": ["unique_user_A", "unique_user_A", "unique_user_B", "unique_user_C"],
        "customer_zip_code_prefix": [1000, 1000, 2000, 3000],
        "customer_city": ["Sao Paulo", "Sao Paulo", "Rio", "Curitiba"],
        "customer_state": ["SP", "SP", "RJ", "PR"]
    })

    items_df = pd.DataFrame({
        "order_id": ["ord_1", "ord_2", "ord_3", "ord_4"],
        "price": [100.0, 50.0, 200.0, 300.0],
        "freight_value": [10.0, 5.0, 20.0, 30.0]
    })

    return orders_df, customers_df, items_df


def test_compute_rfm_metrics_delivered_only(sample_data):
    # Arrange
    orders_df, customers_df, items_df = sample_data
    snapshot_date = pd.Timestamp("2018-08-21 10:00:00")

    # Act
    rfm = compute_rfm_metrics(orders_df, customers_df, items_df, snapshot_date=snapshot_date)

    # Assert
    # Customer C only had canceled order, so must not appear in RFM
    assert "unique_user_C" not in rfm["customer_unique_id"].values
    assert len(rfm) == 2


def test_compute_rfm_metrics_customer_unique_id(sample_data):
    # Arrange
    orders_df, customers_df, items_df = sample_data
    snapshot_date = pd.Timestamp("2018-08-21 10:00:00")

    # Act
    rfm = compute_rfm_metrics(orders_df, customers_df, items_df, snapshot_date=snapshot_date)

    # Assert: User A has 2 orders (ord_1: 110, ord_2: 55 = 165 total), recency = 1 day (Aug 20 to Aug 21)
    user_a = rfm[rfm["customer_unique_id"] == "unique_user_A"].iloc[0]
    assert user_a["frequency"] == 2
    assert pytest.approx(user_a["monetary"], rel=1e-3) == 165.0
    assert user_a["recency"] == 1

    # User B has 1 order (ord_3: 220 total), recency = 37 days (July 15 to Aug 21)
    user_b = rfm[rfm["customer_unique_id"] == "unique_user_B"].iloc[0]
    assert user_b["frequency"] == 1
    assert pytest.approx(user_b["monetary"], rel=1e-3) == 220.0
    assert user_b["recency"] == 37


def test_score_and_segment_rfm():
    # Arrange
    rfm_df = pd.DataFrame({
        "customer_unique_id": [f"user_{i}" for i in range(10)],
        "recency": [10, 20, 50, 80, 120, 150, 200, 250, 300, 400],
        "frequency": [3, 2, 2, 1, 1, 1, 1, 1, 2, 1],
        "monetary": [500.0, 300.0, 250.0, 200.0, 150.0, 120.0, 100.0, 80.0, 50.0, 30.0]
    })

    # Act
    segmented = score_and_segment_rfm(rfm_df)

    # Assert
    assert "r_score" in segmented.columns
    assert "f_score" in segmented.columns
    assert "m_score" in segmented.columns
    assert "segment" in segmented.columns
    assert segmented["segment"].isna().sum() == 0
    # Top user (high recency score, frequency 3, high spend) should be Champions
    top_user = segmented[segmented["customer_unique_id"] == "user_0"].iloc[0]
    assert top_user["segment"] == "Champions"


def test_generate_rfm_summary():
    # Arrange
    segmented_df = pd.DataFrame({
        "customer_unique_id": ["u1", "u2", "u3", "u4"],
        "recency": [10, 20, 200, 400],
        "frequency": [2, 2, 1, 1],
        "monetary": [400.0, 300.0, 150.0, 50.0],
        "segment": ["Champions", "Champions", "Need Attention", "Hibernating"]
    })

    # Act
    summary = generate_rfm_summary(segmented_df)

    # Assert
    assert len(summary) == 3
    assert summary["customer_count"].sum() == 4
    assert pytest.approx(summary["customer_pct"].sum(), abs=1e-2) == 100.0
    assert pytest.approx(summary["monetary_pct"].sum(), abs=1e-2) == 100.0
    assert "action_plan" in summary.columns
    assert summary["action_plan"].isna().sum() == 0


def test_rfm_summary_csv_file_integrity():
    # Arrange
    summary_path = Path(__file__).resolve().parent.parent / "dashboard" / "rfm_summary.csv"

    # Act
    assert summary_path.exists(), f"{summary_path} does not exist!"
    df = pd.read_csv(summary_path)

    # Assert
    expected_cols = [
        "segment", "customer_count", "avg_recency", "avg_frequency",
        "avg_monetary", "total_monetary", "customer_pct", "monetary_pct", "action_plan"
    ]
    for col in expected_cols:
        assert col in df.columns, f"Missing column: {col}"

    assert len(df) == 7
    assert df["customer_count"].sum() == 93358
    assert pytest.approx(df["customer_pct"].sum(), abs=0.1) == 100.0
    assert pytest.approx(df["monetary_pct"].sum(), abs=0.1) == 100.0
    assert df.isna().sum().sum() == 0
