"""
data_analysis.py
----------------
Loads, validates, filters and summarises the CSV data using Pandas.
"""

import pandas as pd

import risk_calculator

REQUIRED_COLUMNS = ["Date", "Location", "Rainfall_mm",
                    "Water_Level_m", "Danger_Level_m"]
NUMBER_COLUMNS = ["Rainfall_mm", "Water_Level_m", "Danger_Level_m"]
ALL_LOCATIONS = "All Locations"


def load_data(path):
    """
    Read and clean a CSV file.

    Returns (dataframe, warnings) where warnings is a list of text messages.
    Raises ValueError if the file cannot be used at all.

    Important: missing numbers are kept as NaN. They are NOT replaced by 0,
    because 0 can be a real measurement.
    """
    warnings = []

    # 1. Read the file
    try:
        df = pd.read_csv(path)
    except pd.errors.EmptyDataError:
        raise ValueError("The file is empty.")
    except Exception as error:
        raise ValueError(f"Could not read the file as CSV: {error}")

    df.columns = [str(c).strip() for c in df.columns]

    # 2. Check columns and rows
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError("Missing required column(s): " + ", ".join(missing)
                         + "\nRequired columns: " + ", ".join(REQUIRED_COLUMNS))
    if df.empty:
        raise ValueError("The file has column names but no data rows.")
    df = df[REQUIRED_COLUMNS].copy()

    # 3. Convert Date column. Rows with an unreadable date are removed
    #    because they cannot be placed on a timeline.
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    bad_dates = int(df["Date"].isna().sum())
    if bad_dates:
        warnings.append(f"{bad_dates} row(s) removed: missing or invalid Date.")
        df = df.dropna(subset=["Date"])

    # 4. Location: a blank location gets the label "Unknown"
    df["Location"] = df["Location"].fillna("Unknown").astype(str).str.strip()

    # 5. Convert number columns. Text like "abc" becomes NaN.
    for col in NUMBER_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")
        missing_count = int(df[col].isna().sum())
        if missing_count:
            warnings.append(f"{col}: {missing_count} missing/invalid value(s) "
                            "kept as empty (not replaced with 0).")
        # Negative values are not physically valid here -> treat as missing
        negative = df[col] < 0
        if negative.sum():
            warnings.append(f"{col}: {int(negative.sum())} negative value(s) "
                            "treated as invalid.")
            df.loc[negative, col] = float("nan")

    if df.empty:
        raise ValueError("No valid rows left after checking the Date column.")

    df = df.sort_values("Date", kind="stable").reset_index(drop=True)
    return df, warnings


def get_locations(df):
    """List of location names, starting with 'All Locations'."""
    return [ALL_LOCATIONS] + sorted(df["Location"].unique().tolist())


def filter_by_location(df, location):
    """Return only the rows for one location (or all rows)."""
    if location in (None, "", ALL_LOCATIONS):
        return df.reset_index(drop=True)
    return df[df["Location"] == location].reset_index(drop=True)


def summary_stats(df):
    """Average, min, max (ignoring empty values) for rainfall and water level."""
    stats = {}
    for col in ["Rainfall_mm", "Water_Level_m"]:
        stats[col] = {
            "average": df[col].mean(),
            "minimum": df[col].min(),
            "maximum": df[col].max(),
            "count": int(df[col].count()),
        }
    return stats


def add_risk_scores(df, rainfall_threshold, danger_override=None):
    """
    Return a copy of df with risk columns added.
    If danger_override is given, it is used instead of the Danger_Level_m
    column from the file.
    """
    result = df.copy()
    if danger_override is None:
        danger = result["Danger_Level_m"].to_numpy()
    else:
        danger = float(danger_override)

    scores = risk_calculator.calculate_scores(
        result["Rainfall_mm"].to_numpy(),
        result["Water_Level_m"].to_numpy(),
        danger,
        rainfall_threshold,
    )
    result["Rainfall_Threshold_mm"] = rainfall_threshold
    result["Rainfall_Score"] = scores["rainfall_score"]
    result["Water_Level_Score"] = scores["water_score"]
    result["Rainfall_Contribution"] = scores["rainfall_part"]
    result["Water_Level_Contribution"] = scores["water_part"]
    result["Risk_Score"] = scores["risk_score"]
    result["Risk_Category"] = scores["category"]
    if danger_override is not None:
        result["Danger_Level_m"] = float(danger_override)
    return result
