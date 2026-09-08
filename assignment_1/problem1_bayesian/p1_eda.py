"""Problem 1, Q2.c -- exploratory data analysis for the student-performance data.

Produces ``outputs/fig_eda.pdf`` and ``outputs/eda_summary.json``.
Run from the assignment root:  python problem1_bayesian/p1_eda.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.plotstyle import AQUA, BLUE, INK, INK_2, ORANGE, apply_style, tidy  # noqa: E402
from p1_common import FEATURES, MJOB_LEVELS, OUT_DIR, load_data  # noqa: E402


def main() -> None:
    apply_style()
    df = load_data()
    n = len(df)
    g3 = df["G3"]

    summary = {
        "n_students": int(n),
        "n_columns": int(df.shape[1] - 4),  # exclude derived columns
        "G3_mean": float(g3.mean()),
        "G3_sd": float(g3.std()),
        "G3_median": float(g3.median()),
        "G3_min": int(g3.min()),
        "G3_max": int(g3.max()),
        "G3_zero_count": int((g3 == 0).sum()),
        "G3_zero_share": float((g3 == 0).mean()),
        "school_counts": df["school"].value_counts().to_dict(),
        "G3_by_school": df.groupby("school")["G3"].agg(["count", "mean", "std"]).round(2).to_dict("index"),
        "G3_by_mjob": df.groupby("Mjob")["G3"].agg(["count", "mean", "std"]).round(2).to_dict("index"),
        "G3_by_failures": df.groupby("failures")["G3"].agg(["count", "mean"]).round(2).to_dict("index"),
        "G3_by_studytime": df.groupby("studytime")["G3"].agg(["count", "mean"]).round(2).to_dict("index"),
        "G3_by_higher": df.groupby("higher")["G3"].agg(["count", "mean"]).round(2).to_dict("index"),
        "absences_mean_zeroG3": float(df.loc[g3 == 0, "absences"].mean()),
        "absences_mean_posG3": float(df.loc[g3 > 0, "absences"].mean()),
        "absences_max": int(df["absences"].max()),
        "corr_with_G3": df[["failures", "absences", "studytime", "higher", "goout", "Medu"]]
        .corrwith(g3)
        .round(3)
        .to_dict(),
        "features": FEATURES,
    }
    (OUT_DIR / "eda_summary.json").write_text(json.dumps(summary, indent=2))

    # ------------------------------------------------------------------ figure
    fig, axes = plt.subplots(1, 4, figsize=(7.4, 1.9), gridspec_kw={"width_ratios": [1.25, 0.9, 1.2, 1.05], "wspace": 0.42})

    # (a) Histogram of G3 with the zero spike highlighted
    ax = axes[0]
    counts = g3.value_counts().sort_index()
    colors = [ORANGE if k == 0 else BLUE for k in counts.index]
    ax.bar(counts.index, counts.values, width=0.85, color=colors, linewidth=0)
    ax.set_xlabel("final grade G3")
    ax.set_ylabel("students")
    ax.set_title("(a) distribution of G3")
    ax.annotate(f"{summary['G3_zero_count']} zeros\n({100*summary['G3_zero_share']:.0f}%)", xy=(0, counts[0]),
                xytext=(3.5, counts.max() * 0.85), fontsize=7, color=ORANGE,
                arrowprops=dict(arrowstyle="-", color=ORANGE, lw=0.6))
    ax.set_xticks([0, 5, 10, 15, 20])
    tidy(ax)

    # (b) G3 by school (box plots)
    ax = axes[1]
    data = [df.loc[df.school == s, "G3"].values for s in ["GP", "MS"]]
    bp = ax.boxplot(data, widths=0.5, patch_artist=True, showfliers=False,
                    medianprops=dict(color=INK, lw=1), whiskerprops=dict(color=INK_2, lw=0.7),
                    capprops=dict(color=INK_2, lw=0.7), boxprops=dict(lw=0.7, edgecolor=INK_2))
    for patch, c in zip(bp["boxes"], [BLUE, ORANGE]):
        patch.set_facecolor(c)
        patch.set_alpha(0.75)
    for i, s in enumerate(["GP", "MS"]):
        ax.text(i + 1, 20.5, f"n={int((df.school == s).sum())}", ha="center", fontsize=6.5, color=INK_2)
    ax.set_xticks([1, 2], ["GP", "MS"])
    ax.set_ylim(0, 22)
    ax.set_title("(b) G3 by school")
    tidy(ax)

    # (c) G3 by mother's job (mean +- 1 s.e.)
    ax = axes[2]
    grp = df.groupby("Mjob")["G3"]
    means = grp.mean().reindex(MJOB_LEVELS)
    ses = (grp.std() / np.sqrt(grp.count())).reindex(MJOB_LEVELS)
    xs = np.arange(len(MJOB_LEVELS))
    ax.errorbar(xs, means.values, yerr=1.96 * ses.values, fmt="o", color=AQUA, ecolor=AQUA, capsize=2, ms=4, lw=1)
    ax.axhline(g3.mean(), color=INK_2, lw=0.6, ls="--")
    ax.set_xticks(xs, ["home", "health", "other", "services", "teacher"], rotation=30, ha="right")
    ax.set_ylim(7, 14)
    ax.set_title("(c) mean G3 by mother's job")
    tidy(ax)

    # (d) G3 vs failures and study time (means)
    ax = axes[3]
    mf = df.groupby("failures")["G3"].mean()
    ms = df.groupby("studytime")["G3"].mean()
    ax.plot(mf.index, mf.values, "o-", color=BLUE, label="by past failures (0-3)")
    ax.plot(ms.index, ms.values, "s-", color=ORANGE, label="by study time (1-4)")
    ax.set_ylim(4, 13)
    ax.set_xticks([0, 1, 2, 3, 4])
    ax.set_xlabel("level")
    ax.set_title("(d) mean G3 by level")
    ax.legend(loc="lower left", fontsize=6.5)
    tidy(ax)

    fig.savefig(OUT_DIR / "fig_eda.pdf")
    fig.savefig(OUT_DIR / "fig_eda.png")
    print(json.dumps({k: v for k, v in summary.items() if not isinstance(v, dict)}, indent=2))
    print("G3 by school:", summary["G3_by_school"])
    print("G3 by Mjob:", summary["G3_by_mjob"])
    print("Saved", OUT_DIR / "fig_eda.pdf")


if __name__ == "__main__":
    main()
