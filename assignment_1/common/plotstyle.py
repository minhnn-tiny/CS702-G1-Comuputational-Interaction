"""Shared matplotlib styling for all figures in the assignment.

A single, fixed categorical palette is used across problems so that
figures read as one system.  Colours are assigned in fixed slot order and
never cycled: slot 1 (blue) is always the first series / the primary model,
slot 2 (orange) the second, slot 3 (aqua) the third, slot 4 (yellow) the fourth.
Observed data is always drawn in near-black ink.
"""

from __future__ import annotations

import matplotlib as mpl
import matplotlib.pyplot as plt

# Categorical slots (fixed order)
BLUE = "#2a78d6"
ORANGE = "#eb6834"
AQUA = "#1baf7a"
YELLOW = "#eda100"
MAGENTA = "#e87ba4"
VIOLET = "#4a3aa7"
RED = "#e34948"
SERIES = [BLUE, ORANGE, AQUA, YELLOW, MAGENTA, VIOLET, RED]

# Ink and surfaces
INK = "#0b0b0b"
INK_2 = "#52514e"
INK_3 = "#8a8985"
GRID = "#e6e5e1"
SURFACE = "#ffffff"

# Sequential blues (light -> dark)
BLUES = ["#cde2fb", "#9ec5f4", "#6da7ec", "#3987e5", "#256abf", "#184f95", "#0d366b"]


def apply_style() -> None:
    """Apply a compact, print-friendly style suited to an A4 report."""
    mpl.rcParams.update(
        {
            "figure.dpi": 150,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
            "savefig.pad_inches": 0.02,
            "figure.facecolor": SURFACE,
            "axes.facecolor": SURFACE,
            "axes.edgecolor": INK_3,
            "axes.labelcolor": INK,
            "axes.titlecolor": INK,
            "axes.titlesize": 8,
            "axes.titleweight": "semibold",
            "axes.labelsize": 8.5,
            "axes.linewidth": 0.6,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": GRID,
            "grid.linewidth": 0.5,
            "axes.axisbelow": True,
            "xtick.labelsize": 7.5,
            "ytick.labelsize": 7.5,
            "xtick.color": INK_2,
            "ytick.color": INK_2,
            "xtick.major.size": 2.5,
            "ytick.major.size": 2.5,
            "legend.fontsize": 7.5,
            "legend.frameon": False,
            "lines.linewidth": 1.4,
            "lines.markersize": 4,
            "font.family": "sans-serif",
            "font.sans-serif": ["Helvetica Neue", "Helvetica", "Arial", "DejaVu Sans"],
            "font.size": 8.5,
            "mathtext.fontset": "dejavusans",
            "pdf.fonttype": 42,
            "ps.fonttype": 42,
        }
    )


def tidy(ax: plt.Axes, xgrid: bool = False) -> None:
    """Small helper: recessive grid and clean spines."""
    ax.grid(axis="y", color=GRID, linewidth=0.5)
    if xgrid:
        ax.grid(axis="x", color=GRID, linewidth=0.5)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
