"""
RFM Analysis Module for E-Commerce Public Dataset.

This module provides functions to calculate Recency, Frequency, and Monetary (RFM)
metrics, score customers, and segment them into actionable business categories.
"""

from pathlib import Path
from typing import Dict, Tuple
import pandas as pd
import numpy as np


def compute_rfm_metrics(
    orders_df: pd.DataFrame,
    customers_df: pd.DataFrame,
    items_df: pd.DataFrame,
    snapshot_date: pd.Timestamp = None
) -> pd.DataFrame:
    """
    Compute raw Recency, Frequency, and Monetary metrics per unique customer.

    Args:
        orders_df: DataFrame containing order records.
        customers_df: DataFrame containing customer records with customer_unique_id.
        items_df: DataFrame containing order item records with price and freight_value.
        snapshot_date: Reference timestamp for recency calculation. If None,
                       defaults to max purchase timestamp + 1 day.

    Returns:
        DataFrame with columns: ['customer_unique_id', 'recency', 'frequency', 'monetary']
    """
    # 1. Filter valid delivered orders
    delivered = orders_df[orders_df["order_status"] == "delivered"].copy()
    delivered["order_purchase_timestamp"] = pd.to_datetime(delivered["order_purchase_timestamp"])

    # 2. Join customer_unique_id (critical: customer_id is per order, customer_unique_id is per individual)
    delivered = delivered.merge(
        customers_df[["customer_id", "customer_unique_id"]],
        on="customer_id",
        how="inner"
    )

    # 3. Calculate total order value (price + freight) consistent with revenue definition
    items_copy = items_df[["order_id", "price", "freight_value"]].copy()
    items_copy["total_item_value"] = items_copy["price"] + items_copy["freight_value"]
    order_val = items_copy.groupby("order_id")["total_item_value"].sum().rename("order_value")

    delivered = delivered.merge(order_val, on="order_id", how="left")
    # Fill any potential missing values with 0
    delivered["order_value"] = delivered["order_value"].fillna(0.0)

    # 4. Set reference snapshot date
    if snapshot_date is None:
        snapshot_date = delivered["order_purchase_timestamp"].max() + pd.Timedelta(days=1)

    # 5. Fast vectorized aggregation per customer_unique_id
    grouped = delivered.groupby("customer_unique_id")
    rfm = grouped.agg(
        max_date=("order_purchase_timestamp", "max"),
        frequency=("order_id", "nunique"),
        monetary=("order_value", "sum")
    ).reset_index()

    rfm["recency"] = (snapshot_date - rfm["max_date"]).dt.days
    rfm.drop(columns=["max_date"], inplace=True)

    return rfm


def score_and_segment_rfm(rfm_df: pd.DataFrame) -> pd.DataFrame:
    """
    Score R, F, and M and assign actionable business segments.

    Args:
        rfm_df: DataFrame containing customer_unique_id, recency, frequency, monetary.

    Returns:
        DataFrame with added score and segment columns.
    """
    df = rfm_df.copy()

    # R score: 5 quintiles (lower recency is better: 5=most recent, 1=least recent)
    df["r_score"] = pd.qcut(df["recency"], q=5, labels=[5, 4, 3, 2, 1]).astype(int)

    # M score: 5 quintiles (higher monetary is better: 5=highest spend, 1=lowest spend)
    df["m_score"] = pd.qcut(df["monetary"], q=5, labels=[1, 2, 3, 4, 5]).astype(int)

    # F score: discrete mapping due to high concentration of single purchases in marketplace
    def map_f_score(f: int) -> int:
        if f >= 3:
            return 5
        elif f == 2:
            return 3
        return 1

    df["f_score"] = df["frequency"].apply(map_f_score)
    df["rfm_score"] = (
        df["r_score"].astype(str) + df["f_score"].astype(str) + df["m_score"].astype(str)
    )

    # Segment mapping logic tailored for e-commerce with low repeat frequency
    def assign_segment(row: pd.Series) -> str:
        r = row["r_score"]
        f = row["frequency"]
        m = row["m_score"]

        # 1. Champions: Repeat buyers who bought recently with solid spend
        if f >= 2 and r >= 4 and m >= 3:
            return "Champions"

        # 2. Loyal Customers: Other active repeat buyers
        elif f >= 2 and r >= 3:
            return "Loyal Customers"

        # 3. At Risk: High-value past spenders (m>=4) or repeat buyers (f>=2) slipping away (r<=2)
        elif (f >= 2 and r <= 2) or (m >= 4 and r <= 2):
            return "At Risk"

        # 4. Potential Loyalists: Recent one-time buyers with high basket value
        elif r >= 4 and m >= 4:
            return "Potential Loyalists"

        # 5. New Customers: Recent one-time buyers with entry/standard basket value
        elif r >= 4:
            return "New Customers"

        # 6. Need Attention: Mid-recency buyers at risk of becoming inactive
        elif r == 3:
            return "Need Attention"

        # 7. Hibernating: Long-inactive low/mid-spend one-time buyers
        else:
            return "Hibernating"

    df["segment"] = df.apply(assign_segment, axis=1)
    return df


def generate_rfm_summary(df_segmented: pd.DataFrame) -> pd.DataFrame:
    """
    Generate an aggregated summary table per RFM segment.
    """
    total_customers = len(df_segmented)
    total_revenue = df_segmented["monetary"].sum()

    summary = (
        df_segmented.groupby("segment")
        .agg(
            customer_count=("customer_unique_id", "count"),
            avg_recency=("recency", "mean"),
            avg_frequency=("frequency", "mean"),
            avg_monetary=("monetary", "mean"),
            total_monetary=("monetary", "sum")
        )
        .reset_index()
    )

    summary["customer_pct"] = (summary["customer_count"] / total_customers) * 100
    summary["monetary_pct"] = (summary["total_monetary"] / total_revenue) * 100

    # Business action recommendations per segment
    action_plans = {
        "Champions": "Berikan reward loyalitas VIP, early access produk baru, dan layanan prioritas.",
        "Loyal Customers": "Tawarkan program referral, diskon personalisasi, dan rekomendasi cross-sell berkala.",
        "Potential Loyalists": "Kirimkan voucher pembelian kedua (berlaku 30 hari) dan rekomendasi produk komplementer.",
        "New Customers": "Jalankan onboarding email berseri, panduan belanja, dan diskon selamat datang pesanan berikutnya.",
        "Need Attention": "Luncurkan kampanye reaktivasi berbasis urgensi (limited-time discount) dan survei preferensi.",
        "At Risk": "Kirimkan penawaran win-back bernilai tinggi, rekomendasi produk terbaru, dan tanyakan feedback layanan.",
        "Hibernating": "Gunakan promosi otomatis berbiaya rendah (email newsletter berkala); hindari biaya retargeting iklan mahal."
    }
    summary["action_plan"] = summary["segment"].map(action_plans)

    # Order segments logically by strategic priority / monetary contribution
    segment_order = [
        "Champions",
        "Loyal Customers",
        "Potential Loyalists",
        "New Customers",
        "Need Attention",
        "At Risk",
        "Hibernating"
    ]
    summary["order"] = summary["segment"].map(lambda s: segment_order.index(s) if s in segment_order else 99)
    summary = summary.sort_values("order").drop(columns=["order"]).reset_index(drop=True)

    return summary


def run_pipeline(
    data_dir: str = "data",
    output_dir: str = "dashboard"
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run full RFM data pipeline and write outputs to output_dir.
    """
    data_path = Path(data_dir)
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print("Loading raw datasets...")
    orders = pd.read_csv(data_path / "orders_dataset.csv")
    customers = pd.read_csv(data_path / "customers_dataset.csv")
    items = pd.read_csv(data_path / "order_items_dataset.csv")

    print("Computing RFM metrics...")
    rfm_raw = compute_rfm_metrics(orders, customers, items)

    print("Scoring and segmenting customers...")
    rfm_segmented = score_and_segment_rfm(rfm_raw)

    print("Generating RFM summary...")
    rfm_summary = generate_rfm_summary(rfm_segmented)

    # Save summary
    summary_file = out_path / "rfm_summary.csv"
    rfm_summary.to_csv(summary_file, index=False)
    print(f"Saved: {summary_file}")

    # Save customer-level RFM data (useful for deep-dive and distribution charts)
    data_file = out_path / "rfm_data.csv"
    rfm_segmented.to_csv(data_file, index=False)
    print(f"Saved: {data_file}")

    return rfm_segmented, rfm_summary


if __name__ == "__main__":
    run_pipeline()
