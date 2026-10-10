"""
charts.py
---------
Creates Matplotlib figures. The GUI places them inside the window.
Gaps in a line mean the measurement was missing (it is not drawn as zero).
"""

from matplotlib.figure import Figure


def _empty_message(ax):
    ax.text(0.5, 0.5, "No data loaded", ha="center", va="center",
            transform=ax.transAxes, color="gray")
    ax.set_xticks([])
    ax.set_yticks([])


def rainfall_figure(df):
    """Line chart of rainfall over time (one line per location)."""
    fig = Figure(figsize=(4.6, 3.2), dpi=100)
    ax = fig.add_subplot(111)
    if df is None or df.empty:
        _empty_message(ax)
    else:
        for location, group in df.groupby("Location"):
            ax.plot(group["Date"], group["Rainfall_mm"], label=location)
        ax.set_xlabel("Date")
        ax.set_ylabel("Rainfall (mm)")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        fig.autofmt_xdate()
    ax.set_title("Rainfall Trend")
    fig.tight_layout()
    return fig


def water_level_figure(df):
    """Line chart of water level over time, with the danger level as a dashed line."""
    fig = Figure(figsize=(4.6, 3.2), dpi=100)
    ax = fig.add_subplot(111)
    if df is None or df.empty:
        _empty_message(ax)
    else:
        for location, group in df.groupby("Location"):
            line, = ax.plot(group["Date"], group["Water_Level_m"], label=location)
            danger = group["Danger_Level_m"].dropna()
            if not danger.empty:
                ax.axhline(danger.iloc[-1], color=line.get_color(),
                           linestyle="--", alpha=0.6)
        ax.set_xlabel("Date")
        ax.set_ylabel("Water level (m)")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        fig.autofmt_xdate()
    ax.set_title("Water-Level Trend (dashed = danger level)")
    fig.tight_layout()
    return fig
