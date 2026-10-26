"""
Integration tests for Streamlit dashboard rendering and filter integrity.
Follows Arrange-Act-Assert (AAA) pattern.
"""

from pathlib import Path
import pytest
from streamlit.testing.v1 import AppTest

# Root directory of the repository
ROOT_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_FILE = ROOT_DIR / "dashboard" / "dashboard.py"


def test_dashboard_renders_without_exceptions():
    # Arrange: Point AppTest to absolute path of dashboard.py
    assert DASHBOARD_FILE.exists(), f"{DASHBOARD_FILE} not found!"

    # Act: Run full dashboard in headless test environment
    at = AppTest.from_file(str(DASHBOARD_FILE), default_timeout=30)
    at.run()

    # Assert: Verify no uncaught exceptions
    assert not at.exception, f"Dashboard threw unexpected exceptions: {[e.value for e in at.exception]}"
    # Verify expected key components exist
    assert len(at.metric) >= 8, f"Expected at least 8 metrics across sections, found {len(at.metric)}"
    assert len(at.sidebar.selectbox) >= 1, "Expected RFM segment selectbox in sidebar"


def test_dashboard_rfm_segment_filter_interaction():
    # Arrange
    at = AppTest.from_file(str(DASHBOARD_FILE), default_timeout=30)
    at.run()

    # Act: Select 'Champions' segment in sidebar
    rfm_select = at.sidebar.selectbox[0]
    rfm_select.select("Champions")
    at.run()

    # Assert: Dashboard continues to run without exceptions and reflects filtered state
    assert not at.exception, f"Dashboard threw exception after filter selection: {[e.value for e in at.exception]}"
    # Info message should acknowledge the selected segment focus
    info_texts = [inf.value for inf in at.info]
    assert any("Champions" in txt for txt in info_texts), "Selected segment info not displayed"
