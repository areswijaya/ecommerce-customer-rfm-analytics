"""
Automated Scenario & Integration Tests for Customer Segmentation & RFM Dashboard.
Validates zero-crash guarantees, robust error handling, and filter edge cases.
Follows Arrange-Act-Assert (AAA) pattern.
"""

from pathlib import Path
import pytest
import pandas as pd
import numpy as np
from streamlit.testing.v1 import AppTest

ROOT_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_FILE = ROOT_DIR / "dashboard" / "dashboard.py"


def test_scenario_default_render():
    """Scenario 1: Default dashboard load with all global filters intact."""
    # Arrange & Act
    at = AppTest.from_file(str(DASHBOARD_FILE), default_timeout=30)
    at.run()

    # Assert
    assert not at.exception, f"Dashboard threw exceptions on default render: {[e.value for e in at.exception]}"
    # Verify metric cards exist in executive overview and sections
    assert len(at.metric) >= 8, f"Expected at least 8 metrics, got {len(at.metric)}"


def test_scenario_rfm_segment_filters():
    """Scenario 2: Selecting critical segments ('Potential Loyalists' & 'At Risk')."""
    # Arrange
    at = AppTest.from_file(str(DASHBOARD_FILE), default_timeout=30)
    at.run()

    # Act 1: Select Potential Loyalists
    rfm_select = at.sidebar.selectbox[0]
    rfm_select.select("Potential Loyalists")
    at.run()

    # Assert 1
    assert not at.exception, "Exception after selecting Potential Loyalists"
    info_texts = [inf.value for inf in at.info]
    assert any("Potential Loyalists" in txt for txt in info_texts)

    # Act 2: Select At Risk
    rfm_select2 = at.sidebar.selectbox[0]
    rfm_select2.select("At Risk")
    at.run()

    # Assert 2
    assert not at.exception, "Exception after selecting At Risk"
    info_texts = [inf.value for inf in at.info]
    assert any("At Risk" in txt for txt in info_texts)


def test_scenario_uncheck_all_categories_and_select_single():
    """Scenario 3: Deselect 'Pilih Seluruh Kategori' and test specific category multiselect."""
    # Arrange
    at = AppTest.from_file(str(DASHBOARD_FILE), default_timeout=30)
    at.run()

    # Act: Uncheck select-all checkbox
    cat_checkbox = at.sidebar.checkbox[0]
    cat_checkbox.uncheck()
    at.run()

    # Assert: Multiselect appears and dashboard runs without crash
    assert not at.exception, "Exception when unchecking select-all categories"
    assert len(at.sidebar.multiselect) >= 1, "Multiselect for categories did not appear"


def test_scenario_payment_filter_interaction():
    """Scenario 4: Deselect 'Pilih Semua Metode' and filter payment methods."""
    # Arrange
    at = AppTest.from_file(str(DASHBOARD_FILE), default_timeout=30)
    at.run()

    # Act: Uncheck select-all payments checkbox
    pay_checkbox = at.sidebar.checkbox[1]
    pay_checkbox.uncheck()
    at.run()

    # Assert
    assert not at.exception, "Exception when unchecking select-all payment methods"


def test_scenario_seller_economics_spearman_calculation():
    """Scenario 5: Verify seller summary data and finite Spearman correlation."""
    # Arrange
    seller_path = ROOT_DIR / "dashboard" / "seller_summary.csv"
    assert seller_path.exists(), "seller_summary.csv missing!"
    df = pd.read_csv(seller_path)

    # Act
    from scipy import stats
    clean = df.dropna(subset=["total_orders", "avg_review_score"])
    rho, p_val = stats.spearmanr(clean["total_orders"], clean["avg_review_score"])

    # Assert
    assert np.isfinite(rho), "Spearman rho is not finite"
    assert 0.0 <= p_val <= 1.0, f"Invalid p-value: {p_val}"


def test_scenario_number_formatting():
    """Scenario 6: Test Indonesian format helper logic."""
    # Arrange
    from dashboard.dashboard import fmt_id

    # Assert
    assert fmt_id(1234567) == "1.234.567"
    assert fmt_id(1234567, is_currency=True) == "R$ 1.234.567"
    assert fmt_id(1234.56, is_currency=True, decimals=2) == "R$ 1.234,56"
    assert fmt_id(None) == "-"
    assert fmt_id(np.nan) == "-"
