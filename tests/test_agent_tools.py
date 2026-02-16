import pandas as pd

from src.agent.tools import (
    analyze_dive_profile,
    get_dive_summary,
)


def _make_dive_data():
    """Create sample dive data for testing."""
    return pd.DataFrame(
        {
            "dive_number": ["1"] * 5 + ["2"] * 5,
            "trip_name": ["Trip A"] * 10,
            "dive_site_name": ["Reef Site"] * 10,
            "time": [0, 60, 120, 180, 240] * 2,
            "depth": [5, 10, 15, 10, 5, 10, 20, 30, 20, 10],
            "temperature": [25.0] * 10,
            "pressure": [200, 180, 160, 140, 120, 200, 170, 140, 110, 80],
            "rbt": [60, 50, 40, 30, 20, 60, 40, 20, 10, 5],
            "ndl": [99, 80, 60, 40, 30, 99, 60, 20, 10, 5],
            "sac_rate": [15.0] * 10,
            "rating": [4] * 5 + [2] * 5,
        }
    )


def test_get_dive_summary():
    df = _make_dive_data()
    result = get_dive_summary("1", df.to_json())

    assert "Dive 1" in result
    assert "Reef Site" in result
    assert "Trip A" in result
    assert "15.0m" in result  # max depth
    assert "4/5" in result  # rating


def test_get_dive_summary_not_found():
    df = _make_dive_data()
    result = get_dive_summary("999", df.to_json())
    assert "No data found" in result


def test_analyze_dive_profile_adverse():
    df = _make_dive_data()
    result = analyze_dive_profile("2", df.to_json())

    assert "Dive 2" in result
    assert "ADVERSE CONDITIONS" in result


def test_analyze_dive_profile_not_found():
    df = _make_dive_data()
    result = analyze_dive_profile("999", df.to_json())
    assert "No data found" in result
