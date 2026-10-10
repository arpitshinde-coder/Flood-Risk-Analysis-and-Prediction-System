"""
risk_calculator.py
------------------
Calculates an INDICATIVE flood-risk score (0-100) using NumPy.

This is a simple rule-based formula. It is NOT a machine-learning model and
NOT a scientifically validated flood probability or an official warning.

This file does not import tkinter, so it can be reused in other projects.
"""

import numpy as np

# ---------------------------------------------------------------------------
# Settings you can change easily
# ---------------------------------------------------------------------------
RAINFALL_WEIGHT = 0.40          # 40% of the score comes from rainfall
WATER_LEVEL_WEIGHT = 0.60       # 60% of the score comes from water level
DEFAULT_RAINFALL_THRESHOLD = 100.0   # mm (illustrative value only)

# Categories: (minimum score, name). Keep them sorted from highest to lowest.
RISK_CATEGORIES = [
    (75, "Very High Risk"),
    (50, "High Risk"),
    (25, "Moderate Risk"),
    (0, "Low Risk"),
]


def validate_positive_number(value, name):
    """Convert a value to a float and make sure it is a positive number.
    Raises ValueError with a clear message if it is not."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{name} must be a number.")
    if not np.isfinite(number) or number <= 0:
        raise ValueError(f"{name} must be greater than 0.")
    return number


def get_category(score):
    """Return the risk category name for one score."""
    if score is None or np.isnan(score):
        return "Not Available"
    for minimum, name in RISK_CATEGORIES:
        if score >= minimum:
            return name
    return "Not Available"


def calculate_scores(rainfall, water_level, danger_level, rainfall_threshold):
    """
    Calculate flood-risk scores for one or many records.

    rainfall, water_level, danger_level : single numbers, lists or arrays
    rainfall_threshold                  : one positive number (mm)

    Invalid inputs (missing, negative, danger level <= 0) become NaN, so the
    score for that record is NaN too. We never replace them with zero.

    Returns a dictionary of NumPy arrays.
    """
    rainfall_threshold = validate_positive_number(
        rainfall_threshold, "Rainfall threshold")

    rain = np.atleast_1d(np.asarray(rainfall, dtype=float))
    water = np.atleast_1d(np.asarray(water_level, dtype=float))
    danger = np.atleast_1d(np.asarray(danger_level, dtype=float))

    # Mark invalid values as NaN (not a number)
    rain = np.where(np.isfinite(rain) & (rain >= 0), rain, np.nan)
    water = np.where(np.isfinite(water) & (water >= 0), water, np.nan)
    danger = np.where(np.isfinite(danger) & (danger > 0), danger, np.nan)

    # Step 1: normalise each value to a 0-100 scale (capped at 100)
    rainfall_score = np.minimum(rain / rainfall_threshold, 1) * 100
    water_score = np.minimum(water / danger, 1) * 100

    # Step 2: apply the weights
    rainfall_part = RAINFALL_WEIGHT * rainfall_score
    water_part = WATER_LEVEL_WEIGHT * water_score

    # Step 3: add them up
    risk_score = np.round(rainfall_part + water_part, 2)

    categories = [get_category(s) for s in risk_score]

    return {
        "rainfall_score": np.round(rainfall_score, 2),
        "water_score": np.round(water_score, 2),
        "rainfall_part": np.round(rainfall_part, 2),
        "water_part": np.round(water_part, 2),
        "risk_score": risk_score,
        "category": categories,
    }
