"""
test_basic.py - simple checks. Run with:  python test_basic.py
No extra packages needed (uses plain assert).
"""

import os
import tempfile

import numpy as np

import data_analysis as da
import risk_calculator as rc


def test_worked_example():
    # rainfall 60/100 -> 60 ; water 3.6/4.5 -> 80 ; 0.4*60 + 0.6*80 = 72
    r = rc.calculate_scores(60, 3.6, 4.5, 100)
    assert r["risk_score"][0] == 72.0
    assert r["category"][0] == "High Risk"


def test_values_are_capped_at_100():
    r = rc.calculate_scores(500, 10, 4.5, 100)
    assert r["risk_score"][0] == 100.0
    assert r["category"][0] == "Very High Risk"


def test_zero_is_a_valid_measurement():
    r = rc.calculate_scores(0, 0, 4.5, 100)
    assert r["risk_score"][0] == 0.0
    assert r["category"][0] == "Low Risk"


def test_invalid_values_give_nan():
    assert np.isnan(rc.calculate_scores(-5, 3, 4.5, 100)["risk_score"][0])   # negative
    assert np.isnan(rc.calculate_scores(np.nan, 3, 4.5, 100)["risk_score"][0])  # missing
    assert np.isnan(rc.calculate_scores(50, 3, 0, 100)["risk_score"][0])     # danger = 0


def test_invalid_threshold_raises():
    for bad in (0, -10, "abc", None):
        try:
            rc.calculate_scores(10, 1, 4, bad)
        except ValueError:
            continue
        raise AssertionError(f"threshold {bad!r} should be rejected")


def test_category_boundaries():
    assert rc.get_category(24.99) == "Low Risk"
    assert rc.get_category(25) == "Moderate Risk"
    assert rc.get_category(50) == "High Risk"
    assert rc.get_category(75) == "Very High Risk"
    assert rc.get_category(float("nan")) == "Not Available"


def test_sample_file_loads():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sample_flood_data.csv")
    df, warnings = da.load_data(path)
    assert 30 <= len(df) <= 100
    assert len(da.get_locations(df)) == 3          # All + 2 locations
    assert df["Rainfall_mm"].isna().sum() == 1     # missing value was NOT turned into 0
    scored = da.add_risk_scores(df, 100)
    assert scored["Risk_Score"].between(0, 100).sum() == scored["Risk_Score"].notna().sum()


def test_bad_files_are_rejected():
    with tempfile.TemporaryDirectory() as folder:
        empty = os.path.join(folder, "empty.csv")
        open(empty, "w").close()
        wrong = os.path.join(folder, "wrong.csv")
        with open(wrong, "w") as f:
            f.write("Date,Rain\n2025-01-01,5\n")
        for path in (empty, wrong, os.path.join(folder, "missing.csv")):
            try:
                da.load_data(path)
            except ValueError:
                continue
            raise AssertionError(f"{path} should have been rejected")


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for t in tests:
        t()
        print("PASS", t.__name__)
    print(f"\nAll {len(tests)} tests passed.")
