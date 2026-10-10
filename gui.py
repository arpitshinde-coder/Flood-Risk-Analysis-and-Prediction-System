"""
gui.py
------
The Tkinter window. It only handles buttons, labels and tables.
All calculations are done in data_analysis.py and risk_calculator.py.
"""

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import charts
import data_analysis as da
import risk_calculator as rc

APP_TITLE = "Flood Risk Analysis & Prediction System"
DESCRIPTION = ("Analyse historical rainfall and water-level data from a CSV file "
               "and calculate an indicative, rule-based flood-risk score.")
DISCLAIMER = ("This score is INDICATIVE only. It is a simple rule-based "
              "calculation, not a scientifically validated flood probability "
              "and not an official flood warning.")
THRESHOLD_NOTE = ("Thresholds are illustrative unless supplied by a reliable "
                  "local authority.")
SAMPLE_NOTE = ("Note: sample_flood_data.csv contains SIMULATED data, "
               "not official measurements.")
MAX_TABLE_ROWS = 1000   # keeps the table fast for big files


def fmt(value, unit=""):
    """Format a number for display; show N/A for missing values."""
    if value is None or pd.isna(value):
        return "N/A"
    return f"{value:.2f} {unit}".strip()


class FloodApp:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("1050x720")
        ttk.Style().theme_use("clam")

        # --- data held by the app ---
        self.file_path = None
        self.full_df = None      # everything loaded from the CSV
        self.view_df = pd.DataFrame(columns=da.REQUIRED_COLUMNS)  # filtered
        self.scored_df = None    # view_df + risk columns (after Calculate)
        self.selected_pos = None # position of the chosen record
        self.canvases = {}       # chart canvases

        self.build_toolbar()
        self.build_tabs()
        self.refresh_all()

    # ------------------------------------------------------------------
    # Building the window
    # ------------------------------------------------------------------
    def build_toolbar(self):
        bar = ttk.Frame(self.root, padding=8)
        bar.pack(fill="x")
        ttk.Button(bar, text="Load CSV", command=self.load_csv).pack(side="left")
        ttk.Button(bar, text="Reload", command=self.reload_csv).pack(side="left", padx=4)
        ttk.Button(bar, text="Clear", command=self.clear_data).pack(side="left")

        ttk.Label(bar, text="   Location:").pack(side="left")
        self.location_var = tk.StringVar(value=da.ALL_LOCATIONS)
        self.location_combo = ttk.Combobox(bar, textvariable=self.location_var,
                                           state="readonly", width=24,
                                           values=[da.ALL_LOCATIONS])
        self.location_combo.pack(side="left", padx=4)
        self.location_combo.bind("<<ComboboxSelected>>", lambda e: self.refresh_views())

    def build_tabs(self):
        self.tabs = ttk.Notebook(self.root)
        self.tabs.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.tab_dash = ttk.Frame(self.tabs, padding=12)
        self.tab_data = ttk.Frame(self.tabs, padding=8)
        self.tab_stats = ttk.Frame(self.tabs, padding=8)
        self.tab_risk = ttk.Frame(self.tabs, padding=12)
        self.tab_report = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(self.tab_dash, text="Dashboard")
        self.tabs.add(self.tab_data, text="Dataset")
        self.tabs.add(self.tab_stats, text="Historical Analysis")
        self.tabs.add(self.tab_risk, text="Flood-Risk Analysis")
        self.tabs.add(self.tab_report, text="Report")

        self.build_dashboard()
        self.build_dataset_tab()
        self.build_stats_tab()
        self.build_risk_tab()
        self.build_report_tab()

    def build_dashboard(self):
        ttk.Label(self.tab_dash, text=APP_TITLE,
                  font=("Segoe UI", 20, "bold")).pack(anchor="w")
        ttk.Label(self.tab_dash, text=DESCRIPTION, wraplength=900).pack(anchor="w", pady=(4, 2))
        ttk.Label(self.tab_dash, text=SAMPLE_NOTE, foreground="gray").pack(anchor="w", pady=(0, 12))

        box = ttk.LabelFrame(self.tab_dash, text="Overview", padding=12)
        box.pack(fill="x")
        self.dash_vars = {}
        for row, name in enumerate(["File", "Records loaded", "Selected location",
                                    "Latest date", "Latest rainfall",
                                    "Latest water level"]):
            ttk.Label(box, text=name + ":", font=("Segoe UI", 10, "bold")).grid(
                row=row, column=0, sticky="w", pady=3)
            var = tk.StringVar()
            ttk.Label(box, textvariable=var).grid(row=row, column=1, sticky="w", padx=12)
            self.dash_vars[name] = var

    def build_dataset_tab(self):
        top = ttk.Frame(self.tab_data)
        top.pack(fill="x")
        ttk.Button(top, text="Refresh Table", command=self.fill_table).pack(side="left")
        self.validation_var = tk.StringVar()
        ttk.Label(self.tab_data, textvariable=self.validation_var, foreground="#a15c00",
                  wraplength=950, justify="left").pack(fill="x", pady=4)

        frame = ttk.Frame(self.tab_data)
        frame.pack(fill="both", expand=True)
        self.table = ttk.Treeview(frame, columns=da.REQUIRED_COLUMNS, show="headings")
        for col in da.REQUIRED_COLUMNS:
            self.table.heading(col, text=col)
            self.table.column(col, width=140, anchor="center")
        y_scroll = ttk.Scrollbar(frame, orient="vertical", command=self.table.yview)
        x_scroll = ttk.Scrollbar(frame, orient="horizontal", command=self.table.xview)
        self.table.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)
        y_scroll.pack(side="right", fill="y")
        x_scroll.pack(side="bottom", fill="x")
        self.table.pack(fill="both", expand=True)

    def build_stats_tab(self):
        box = ttk.LabelFrame(self.tab_stats, text="Summary Statistics", padding=8)
        box.pack(fill="x")
        headers = ["", "Average", "Minimum", "Maximum", "Valid values"]
        for c, h in enumerate(headers):
            ttk.Label(box, text=h, font=("Segoe UI", 10, "bold")).grid(
                row=0, column=c, padx=14, pady=2)
        self.stat_vars = {}
        for r, (col, label) in enumerate([("Rainfall_mm", "Rainfall (mm)"),
                                          ("Water_Level_m", "Water level (m)")], start=1):
            ttk.Label(box, text=label).grid(row=r, column=0, sticky="w", padx=14)
            self.stat_vars[col] = []
            for c in range(1, 5):
                var = tk.StringVar()
                ttk.Label(box, textvariable=var).grid(row=r, column=c, padx=14)
                self.stat_vars[col].append(var)

        charts_frame = ttk.Frame(self.tab_stats)
        charts_frame.pack(fill="both", expand=True, pady=8)
        self.rain_chart_frame = ttk.Frame(charts_frame)
        self.rain_chart_frame.pack(side="left", fill="both", expand=True)
        self.water_chart_frame = ttk.Frame(charts_frame)
        self.water_chart_frame.pack(side="left", fill="both", expand=True)

    def build_risk_tab(self):
        settings = ttk.LabelFrame(self.tab_risk, text="Settings", padding=8)
        settings.pack(fill="x")

        ttk.Label(settings, text="Rainfall threshold (mm):").grid(row=0, column=0, sticky="w")
        self.rain_threshold_var = tk.StringVar(value=str(rc.DEFAULT_RAINFALL_THRESHOLD))
        ttk.Entry(settings, textvariable=self.rain_threshold_var, width=10).grid(
            row=0, column=1, padx=8, pady=2)

        ttk.Label(settings, text="Danger level override (m):").grid(row=1, column=0, sticky="w")
        self.danger_var = tk.StringVar()
        ttk.Entry(settings, textvariable=self.danger_var, width=10).grid(
            row=1, column=1, padx=8, pady=2)
        ttk.Label(settings, text="(leave empty to use Danger_Level_m from the file)",
                  foreground="gray").grid(row=1, column=2, sticky="w")

        ttk.Label(settings, text=THRESHOLD_NOTE, foreground="gray").grid(
            row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

        ttk.Label(settings, text="Select record:").grid(row=3, column=0, sticky="w", pady=(8, 0))
        self.record_combo = ttk.Combobox(settings, state="readonly", width=40)
        self.record_combo.grid(row=3, column=1, columnspan=2, sticky="w", padx=8, pady=(8, 0))
        ttk.Button(settings, text="Calculate Risk", command=self.calculate_risk).grid(
            row=3, column=3, padx=8, pady=(8, 0))

        # Results
        self.measure_var = tk.StringVar()
        ttk.Label(self.tab_risk, textvariable=self.measure_var,
                  font=("Segoe UI", 11)).pack(anchor="w", pady=(14, 0))
        self.score_var = tk.StringVar(value="--")
        ttk.Label(self.tab_risk, textvariable=self.score_var,
                  font=("Segoe UI", 44, "bold")).pack(pady=(6, 0))
        self.category_var = tk.StringVar()
        self.category_label = ttk.Label(self.tab_risk, textvariable=self.category_var,
                                        font=("Segoe UI", 18, "bold"))
        self.category_label.pack()
        self.explain_var = tk.StringVar()
        ttk.Label(self.tab_risk, textvariable=self.explain_var, justify="left",
                  wraplength=950).pack(anchor="w", pady=12)
        ttk.Label(self.tab_risk, text=DISCLAIMER, foreground="#b00020",
                  wraplength=950, justify="left").pack(anchor="w")

    def build_report_tab(self):
        ttk.Label(self.tab_report, text="Report Summary",
                  font=("Segoe UI", 14, "bold")).pack(anchor="w")
        self.report_text = tk.Text(self.tab_report, height=18, font=("Consolas", 11),
                                   state="disabled", wrap="word")
        self.report_text.pack(fill="both", expand=True, pady=8)
        buttons = ttk.Frame(self.tab_report)
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Export Selected Result (CSV)",
                   command=self.export_selected).pack(side="left")
        ttk.Button(buttons, text="Export All Records With Scores (CSV)",
                   command=self.export_all).pack(side="left", padx=8)

    # ------------------------------------------------------------------
    # Dataset buttons
    # ------------------------------------------------------------------
    def load_csv(self):
        folder = os.path.dirname(os.path.abspath(__file__))
        path = filedialog.askopenfilename(
            title="Select a CSV file", initialdir=folder,
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if path:
            self.read_file(path)

    def reload_csv(self):
        if not self.file_path:
            messagebox.showinfo("Reload", "No file has been loaded yet.")
            return
        self.read_file(self.file_path)

    def read_file(self, path):
        try:
            df, warnings = da.load_data(path)
        except ValueError as error:
            messagebox.showerror("Cannot load file", str(error))
            return
        self.file_path = path
        self.full_df = df
        self.location_combo["values"] = da.get_locations(df)
        self.location_var.set(da.ALL_LOCATIONS)
        self.validation_var.set("\n".join(warnings))
        self.refresh_views()
        if warnings:
            messagebox.showwarning("Data check", "The file was loaded, but:\n\n"
                                   + "\n".join(warnings))

    def clear_data(self):
        self.file_path = None
        self.full_df = None
        self.location_combo["values"] = [da.ALL_LOCATIONS]
        self.location_var.set(da.ALL_LOCATIONS)
        self.validation_var.set("")
        self.refresh_all()

    # ------------------------------------------------------------------
    # Refreshing what is shown
    # ------------------------------------------------------------------
    def refresh_all(self):
        self.refresh_views()

    def refresh_views(self):
        """Apply the location filter and update every tab."""
        if self.full_df is None:
            self.view_df = pd.DataFrame(columns=da.REQUIRED_COLUMNS)
        else:
            self.view_df = da.filter_by_location(self.full_df, self.location_var.get())
        self.scored_df = None
        self.selected_pos = None
        self.update_dashboard()
        self.fill_table()
        self.update_stats()
        self.update_record_list()
        self.reset_risk_display()

    def has_data(self):
        return self.view_df is not None and not self.view_df.empty

    def update_dashboard(self):
        v = self.dash_vars
        v["File"].set(os.path.basename(self.file_path) if self.file_path else "None")
        v["Records loaded"].set(str(len(self.view_df)))
        v["Selected location"].set(self.location_var.get())
        if self.has_data():
            last = self.view_df.iloc[-1]
            v["Latest date"].set(last["Date"].strftime("%Y-%m-%d"))
            v["Latest rainfall"].set(fmt(last["Rainfall_mm"], "mm"))
            v["Latest water level"].set(fmt(last["Water_Level_m"], "m"))
        else:
            for key in ["Latest date", "Latest rainfall", "Latest water level"]:
                v[key].set("N/A")

    def fill_table(self):
        self.table.delete(*self.table.get_children())
        if not self.has_data():
            return
        for _, row in self.view_df.head(MAX_TABLE_ROWS).iterrows():
            self.table.insert("", "end", values=(
                row["Date"].strftime("%Y-%m-%d"), row["Location"],
                fmt(row["Rainfall_mm"]), fmt(row["Water_Level_m"]),
                fmt(row["Danger_Level_m"])))

    def update_stats(self):
        if self.has_data():
            stats = da.summary_stats(self.view_df)
            for col, vars_ in self.stat_vars.items():
                s = stats[col]
                vars_[0].set(fmt(s["average"]))
                vars_[1].set(fmt(s["minimum"]))
                vars_[2].set(fmt(s["maximum"]))
                vars_[3].set(str(s["count"]))
        else:
            for vars_ in self.stat_vars.values():
                for var in vars_:
                    var.set("N/A")
        self.show_figure(self.rain_chart_frame, charts.rainfall_figure(self.view_df), "rain")
        self.show_figure(self.water_chart_frame, charts.water_level_figure(self.view_df), "water")

    def show_figure(self, parent, fig, key):
        """Replace the old chart with a new one."""
        if key in self.canvases:
            self.canvases[key].get_tk_widget().destroy()
        canvas = FigureCanvasTkAgg(fig, master=parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        self.canvases[key] = canvas

    def update_record_list(self):
        if self.has_data():
            items = [f"{r['Date']:%Y-%m-%d} | {r['Location']}"
                     for _, r in self.view_df.iterrows()]
            self.record_combo["values"] = items
            self.record_combo.current(len(items) - 1)   # latest record
        else:
            self.record_combo["values"] = []
            self.record_combo.set("")

    def reset_risk_display(self):
        self.measure_var.set("")
        self.score_var.set("--")
        self.category_var.set("")
        self.explain_var.set("")
        self.set_report("No analysis yet. Go to 'Flood-Risk Analysis' and click "
                        "'Calculate Risk'.")

    # ------------------------------------------------------------------
    # Risk calculation
    # ------------------------------------------------------------------
    def calculate_risk(self):
        if not self.has_data():
            messagebox.showinfo("No data", "Please load a CSV file first.")
            return
        pos = self.record_combo.current()
        if pos < 0:
            messagebox.showinfo("Select record", "Please select a record.")
            return

        # Read and validate the settings typed by the user
        try:
            threshold = rc.validate_positive_number(
                self.rain_threshold_var.get(), "Rainfall threshold")
            override = None
            if self.danger_var.get().strip():
                override = rc.validate_positive_number(
                    self.danger_var.get(), "Danger level override")
        except ValueError as error:
            messagebox.showerror("Invalid setting", str(error))
            return

        self.scored_df = da.add_risk_scores(self.view_df, threshold, override)
        self.selected_pos = pos
        row = self.scored_df.iloc[pos]

        self.measure_var.set(
            f"{row['Date']:%Y-%m-%d} | {row['Location']} | "
            f"Rainfall: {fmt(row['Rainfall_mm'], 'mm')} | "
            f"Water level: {fmt(row['Water_Level_m'], 'm')} | "
            f"Danger level: {fmt(row['Danger_Level_m'], 'm')}")

        if pd.isna(row["Risk_Score"]):
            self.score_var.set("N/A")
            self.category_var.set("Not Available")
            self.explain_var.set("The score cannot be calculated because rainfall, "
                                 "water level or danger level is missing or invalid "
                                 "for this record.")
        else:
            self.score_var.set(f"{row['Risk_Score']:.1f} / 100")
            self.category_var.set(row["Risk_Category"])
            self.explain_var.set(
                f"Rainfall: {fmt(row['Rainfall_mm'], 'mm')} vs threshold "
                f"{threshold:g} mm -> rainfall score {row['Rainfall_Score']:.1f} "
                f"x {rc.RAINFALL_WEIGHT:.0%} = {row['Rainfall_Contribution']:.1f} points\n"
                f"Water level: {fmt(row['Water_Level_m'], 'm')} vs danger level "
                f"{fmt(row['Danger_Level_m'], 'm')} -> water-level score "
                f"{row['Water_Level_Score']:.1f} x {rc.WATER_LEVEL_WEIGHT:.0%} = "
                f"{row['Water_Level_Contribution']:.1f} points\n"
                f"Total = {row['Risk_Score']:.1f} points")
        self.update_report(row)

    def update_report(self, row):
        lines = [
            "FLOOD RISK ANALYSIS - REPORT SUMMARY",
            "=" * 40,
            f"Date           : {row['Date']:%Y-%m-%d}",
            f"Location       : {row['Location']}",
            f"Rainfall       : {fmt(row['Rainfall_mm'], 'mm')}",
            f"Water level    : {fmt(row['Water_Level_m'], 'm')}",
            f"Danger level   : {fmt(row['Danger_Level_m'], 'm')}",
            f"Risk score     : {fmt(row['Risk_Score'])} / 100",
            f"Risk category  : {row['Risk_Category']}",
            "",
            DISCLAIMER,
            THRESHOLD_NOTE,
        ]
        self.set_report("\n".join(lines))

    def set_report(self, text):
        self.report_text.configure(state="normal")
        self.report_text.delete("1.0", "end")
        self.report_text.insert("1.0", text)
        self.report_text.configure(state="disabled")

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------
    def export_selected(self):
        if self.scored_df is None:
            messagebox.showinfo("Export", "Please click 'Calculate Risk' first.")
            return
        self.save_csv(self.scored_df.iloc[[self.selected_pos]])

    def export_all(self):
        if self.scored_df is None:
            messagebox.showinfo("Export", "Please click 'Calculate Risk' first.")
            return
        self.save_csv(self.scored_df)

    def save_csv(self, df):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV files", "*.csv")],
            initialfile="flood_risk_results.csv")
        if not path:
            return
        out = df.copy()
        out["Date"] = out["Date"].dt.strftime("%Y-%m-%d")
        try:
            out.to_csv(path, index=False)
        except OSError as error:
            messagebox.showerror("Export failed", str(error))
            return
        messagebox.showinfo("Export", f"Saved {len(out)} row(s) to:\n{path}")
