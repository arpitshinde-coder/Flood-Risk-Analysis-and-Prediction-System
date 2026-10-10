# Flood Risk Analysis & Prediction System

A simple desktop mini-project (Python + Tkinter) that analyses historical rainfall and
water-level data from a CSV file and calculates an **indicative, rule-based flood-risk score**.

> The score is **not** a scientifically validated flood probability, **not** a machine-learning
> prediction and **not** an official flood warning.

## Files

| File | Purpose |
|---|---|
| `main.py` | Starts the app |
| `gui.py` | Tkinter window (buttons, tabs, table) |
| `data_analysis.py` | Load, validate, filter and summarise data (Pandas) |
| `risk_calculator.py` | Risk score formula (NumPy). No GUI code, reusable |
| `charts.py` | Rainfall and water-level charts (Matplotlib) |
| `sample_flood_data.csv` | **Simulated** sample data (60 rows, 2 locations) |
| `test_basic.py` | Small set of checks |
| `requirements.txt` | Python packages |

## Installation

1. Install Python 3.9 or newer (Tkinter is included with the Windows/macOS installers from python.org).
   - On Ubuntu/Debian, if Tkinter is missing: `sudo apt install python3-tk`
2. Open a terminal in the `FloodRiskAnalysis` folder.
3. (Optional) create a virtual environment:
   ```
   python -m venv venv
   venv\Scripts\activate        (Windows)
   source venv/bin/activate     (macOS / Linux)
   ```
4. Install the packages:
   ```
   pip install -r requirements.txt
   ```

## How to run

```
python main.py
```

1. Click **Load CSV** and choose `sample_flood_data.csv`.
2. **Dashboard** shows record count, location and the latest measurements.
3. **Dataset** shows the table. **Historical Analysis** shows statistics and two trend charts.
4. Use the **Location** drop-down (top) to filter by location.
5. In **Flood-Risk Analysis**: set the rainfall threshold (and optionally a danger-level override),
   pick a record, click **Calculate Risk**.
6. **Report** shows the summary and lets you export to CSV.

## How Pandas and NumPy are used

**Pandas** (`data_analysis.py`)
- `read_csv` – read the file
- `to_datetime`, `to_numeric` (with `errors="coerce"`) – convert dates and numbers; bad values become `NaN`
- `mean()`, `min()`, `max()` – summary statistics (empty values are ignored, not counted as 0)
- Boolean filtering – filter by location
- `to_csv` – export results

**NumPy** (`risk_calculator.py`)
- `np.asarray`, `np.where`, `np.isfinite` – check values and mark invalid ones as `NaN`
- `np.minimum` – cap each normalised value at 1 (100%)
- Array arithmetic – calculate scores for all records at once
- `np.round` – round results

## The flood-risk formula

```
Rainfall Score    = min(Rainfall / Rainfall Threshold, 1) x 100
Water-Level Score = min(Water Level / Danger Level, 1)    x 100
Flood Risk Score  = 0.40 x Rainfall Score + 0.60 x Water-Level Score
```

| Score | Category |
|---|---|
| 0 – 24.99 | Low Risk |
| 25 – 49.99 | Moderate Risk |
| 50 – 74.99 | High Risk |
| 75 – 100 | Very High Risk |

**Worked example** – rainfall 60 mm, threshold 100 mm, water level 3.6 m, danger level 4.5 m:

- Rainfall Score = min(60 / 100, 1) x 100 = **60**
- Water-Level Score = min(3.6 / 4.5, 1) x 100 = **80**
- Flood Risk Score = 0.40 x 60 + 0.60 x 80 = 24 + 48 = **72** -> **High Risk**

Values above the threshold are capped at 100, so the final score never goes above 100.
The default rainfall threshold (100 mm) is only an illustrative value. Use a threshold from a
reliable local authority for any real-world interpretation.

**Easy things to change** (top of `risk_calculator.py`): `RAINFALL_WEIGHT`, `WATER_LEVEL_WEIGHT`,
`DEFAULT_RAINFALL_THRESHOLD`, and the `RISK_CATEGORIES` list.

## Using your own dataset

Your CSV must have these exact column names (any order, extra columns are ignored):

```
Date,Location,Rainfall_mm,Water_Level_m,Danger_Level_m
2025-06-01,My River,12.5,1.8,5.0
```

- Date format `YYYY-MM-DD` works best.
- Rainfall and water level must be numbers >= 0; `Danger_Level_m` must be > 0.
- Leave a cell empty if a value is unknown. **Do not type 0 for missing data**, because 0 is a valid measurement.

## Data checks and error handling

| Situation | What the app does |
|---|---|
| Empty file / not a CSV / file not found | Error message, nothing is loaded |
| Required column missing | Error message listing the missing columns |
| Invalid or missing Date | Those rows are removed and a warning is shown |
| Missing or non-numeric measurement | Kept as empty (never changed to 0); warning shown; charts show a gap |
| Negative measurement | Treated as invalid (empty); warning shown |
| Danger level <= 0 or empty | Score for that record shows "N/A" |
| Rainfall threshold or override not a positive number | Error message, no calculation |
| Click Calculate / Export with no data | Friendly information message |

## Testing

Automatic checks (no extra packages needed):

```
python test_basic.py
```

Manual checks:
1. Load `sample_flood_data.csv` – you should see 60 records, and a warning about 1 missing rainfall value.
2. Choose "Riverside Town" in the Location drop-down – 30 records.
3. Select 2025-06-10, rainfall threshold 100 – expect score 100 (Very High Risk).
4. Enter `-5` as the threshold – an error message appears.
5. Make a copy of the CSV, rename `Rainfall_mm` to `Rain`, load it – "Missing required column" error.
6. Click **Clear** – everything resets.

## Limitations

- Rule-based formula only; it does not learn from data or forecast future floods.
- Works only on CSV files you load. No live data, weather APIs, sensors, alerts or maps.
- The sample data is simulated and not from any official source.
- Thresholds are illustrative unless supplied by a reliable local authority.

## Ideas for later (not in this version)

Different weights per location, extra input columns (e.g. soil moisture), saving settings, or an
optional model – the calculation code is separate from the GUI so it can be extended.
