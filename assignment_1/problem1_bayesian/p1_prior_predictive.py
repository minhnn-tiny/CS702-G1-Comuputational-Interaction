"""Problem 1, Q2.a/Q2.b -- prior predictive checks for both models.

For each model we simulate final grades from the *prior* (no data used for
fitting) under the initial, vague priors and under the revised, weakly
informative priors, and check whether the simulated G3 values are plausible for
a 0-20 grade scale.

Produces ``outputs/fig_prior_predictive.pdf`` and ``outputs/prior_predictive.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import jax
import matplotlib.pyplot as plt
import numpy as np
from jax import random
from numpyro.infer import Predictive

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.plotstyle import BLUE, INK, INK_2, ORANGE, apply_style, tidy  # noqa: E402
from p1_common import MODELS, MODEL_TITLES, OUT_DIR, PRIORS, get_arrays, load_data  # noqa: E402

NUM_SIM = 1000  # simulated data sets per (model, prior)


def prior_predictive(model, prior, X, school, mjob, key):
    pred = Predictive(model, num_samples=NUM_SIM)
    samples = pred(key, X, school, mjob, y=None, prior=prior)
    return np.asarray(samples["G3"])  # (NUM_SIM, n)


def main() -> None:
    apply_style()
    df = load_data()
    X, school, mjob, y, _, _ = get_arrays(df)
    y = np.asarray(y)
    key = random.PRNGKey(2026)

    results = {}
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.0), sharey=True)
    grid = np.linspace(-40, 60, 400)

    for ax, (name, model) in zip(axes, MODELS.items()):
        for prior, color, ls in (("initial", ORANGE, "--"), ("revised", BLUE, "-")):
            key, sub = random.split(key)
            sims = prior_predictive(model, prior, X, school, mjob, sub)
            flat = sims.ravel()
            outside = float(np.mean((flat < 0) | (flat > 20)))
            ds_means = sims.mean(axis=1)
            ds_sds = sims.std(axis=1)
            results[f"{name}/{prior}"] = {
                "hyperparameters": PRIORS[prior],
                "share_outside_0_20": outside,
                "q05_q95_of_G3": [float(np.quantile(flat, 0.05)), float(np.quantile(flat, 0.95))],
                "dataset_mean_q05_q95": [float(np.quantile(ds_means, 0.05)), float(np.quantile(ds_means, 0.95))],
                "dataset_sd_q05_q95": [float(np.quantile(ds_sds, 0.05)), float(np.quantile(ds_sds, 0.95))],
            }
            # Pooled prior-predictive density of individual grades (histogram)
            hist, edges = np.histogram(flat, bins=np.arange(-40, 61, 2), density=True)
            centers = 0.5 * (edges[1:] + edges[:-1])
            ax.plot(centers, hist, color=color, ls=ls, lw=1.3,
                    label=f"{prior} priors ({100*outside:.0f}% outside 0-20)")
        ax.axvspan(0, 20, color=INK_2, alpha=0.08, lw=0)
        ax.axvline(0, color=INK_2, lw=0.6)
        ax.axvline(20, color=INK_2, lw=0.6)
        ax.set_xlim(-40, 60)
        ax.set_xlabel("simulated final grade G3")
        ax.set_title(MODEL_TITLES[name])
        ax.legend(loc="upper right", fontsize=6.5)
        tidy(ax)
    axes[0].set_ylabel("prior predictive density")
    fig.savefig(OUT_DIR / "fig_prior_predictive.pdf")
    fig.savefig(OUT_DIR / "fig_prior_predictive.png")
    (OUT_DIR / "prior_predictive.json").write_text(json.dumps(results, indent=2))
    print(json.dumps(results, indent=2))
    print("Saved", OUT_DIR / "fig_prior_predictive.pdf")


if __name__ == "__main__":
    main()
