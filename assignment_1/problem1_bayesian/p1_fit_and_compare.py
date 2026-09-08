"""Problem 1, Q3 -- posterior inference, posterior predictive checks and LOO.

Fits both models with NUTS (4 chains), reports convergence diagnostics, draws
posterior predictive samples of G3, summarises key parameters (mean, sd, 95%
HDI) and compares the models with PSIS-LOO cross-validation (ArviZ).

Outputs (in ``outputs/``):
    fig_ppc.pdf, fig_posterior.pdf, posterior_summary.csv, diagnostics.json,
    ppc_stats.json, loo_compare.csv, loo_results.json
Run from the assignment root:  python problem1_bayesian/p1_fit_and_compare.py
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpyro

numpyro.set_host_device_count(4)  # must precede any JAX computation

import arviz as az  # noqa: E402
import jax  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from jax import random  # noqa: E402
from numpyro.diagnostics import summary as numpyro_summary  # noqa: E402
from numpyro.infer import MCMC, NUTS, Predictive  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.plotstyle import AQUA, BLUE, INK, INK_2, ORANGE, apply_style, tidy  # noqa: E402
from p1_common import (  # noqa: E402
    FEATURES,
    FEATURE_LABELS,
    MJOB_LEVELS,
    MODEL_TITLES,
    MODELS,
    OUT_DIR,
    SCHOOL_LEVELS,
    get_arrays,
    load_data,
)

NUM_WARMUP, NUM_SAMPLES, NUM_CHAINS = 1000, 1500, 4
SEED = 2026
HDI_PROB = 0.95


# --------------------------------------------------------------------------- #
def fit_model(name, model, X, school, mjob, y, key):
    t0 = time.time()
    kernel = NUTS(model, target_accept_prob=0.99)
    mcmc = MCMC(kernel, num_warmup=NUM_WARMUP, num_samples=NUM_SAMPLES, num_chains=NUM_CHAINS, progress_bar=False)
    mcmc.run(key, X, school, mjob, y=y)
    print(f"[{name}] sampled {NUM_CHAINS}x{NUM_SAMPLES} draws in {time.time() - t0:.1f}s")
    return mcmc


def diagnostics(mcmc, exclude=("mu",)):
    """Max R-hat and min ESS over all (non-deterministic) sample sites."""
    samples = mcmc.get_samples(group_by_chain=True)
    samples = {k: v for k, v in samples.items() if k not in exclude}
    stats = numpyro_summary(samples, prob=HDI_PROB, group_by_chain=True)
    rhat_max, ess_min, per_site = 0.0, np.inf, {}
    for site, st in stats.items():
        r = float(np.max(st["r_hat"]))
        e = float(np.min(st["n_eff"]))
        per_site[site] = {"r_hat_max": r, "ess_min": e}
        rhat_max, ess_min = max(rhat_max, r), min(ess_min, e)
    div = int(np.sum(np.asarray(mcmc.get_extra_fields()["diverging"])))
    return {"r_hat_max": rhat_max, "ess_min": ess_min, "divergences": div, "per_site": per_site}


def to_idata(name, mcmc, ppc, n):
    coords = {"feature": FEATURES, "school": SCHOOL_LEVELS, "mjob": MJOB_LEVELS, "student": np.arange(n)}
    dims = {"beta": ["feature"], "a_school": ["school"], "a_mjob": ["mjob"], "z_school": ["school"],
            "z_mjob": ["mjob"], "mu": ["student"], "G3": ["student"]}
    idata = az.from_numpyro(mcmc, posterior_predictive=ppc, log_likelihood=True, coords=coords, dims=dims)
    return idata


def param_table(name, mcmc, means, sds):
    """Posterior mean, sd and 95% HDI for the key parameters (human-readable rows)."""
    s = mcmc.get_samples()
    rows = []

    def add(label, draws, note=""):
        draws = np.asarray(draws)
        lo, hi = hdi(draws, HDI_PROB)
        rows.append(dict(model=name, parameter=label, mean=float(draws.mean()), sd=float(draws.std()),
                         hdi_low=float(lo), hdi_high=float(hi), note=note))

    add("alpha (intercept)", s["alpha"], "grade points")
    for k, f in enumerate(FEATURES):
        unit = "yes vs no" if f == "higher" else f"per 1 SD ({sds[f]:.2f})"
        add(f"beta[{FEATURE_LABELS[f]}]", s["beta"][:, k], unit)
    add("sigma (residual sd)", s["sigma"], "grade points")
    if "a_school" in s:
        add("sigma_school", s["sigma_school"], "between-school sd")
        add("sigma_mjob", s["sigma_mjob"], "between-Mjob sd")
        for j, lvl in enumerate(SCHOOL_LEVELS):
            add(f"a_school[{lvl}]", s["a_school"][:, j], "varying intercept")
        for m, lvl in enumerate(MJOB_LEVELS):
            add(f"a_mjob[{lvl}]", s["a_mjob"][:, m], "varying intercept")
    return pd.DataFrame(rows)


def ppc_stats(name, ppc_draws, y, df):
    """Posterior predictive checks on summary statistics (Bayesian p-values)."""
    yrep = ppc_draws  # (S, n)
    stats = {
        "mean": (y.mean(), yrep.mean(axis=1)),
        "sd": (y.std(), yrep.std(axis=1)),
        "share_zero": ((y == 0).mean(), (yrep < 0.5).mean(axis=1)),
        "share_below_0": ((y < 0).mean(), (yrep < 0).mean(axis=1)),
        "share_above_20": ((y > 20).mean(), (yrep > 20).mean(axis=1)),
        "min": (y.min(), yrep.min(axis=1)),
        "max": (y.max(), yrep.max(axis=1)),
    }
    out = {}
    for k, (obs, rep) in stats.items():
        out[k] = {"observed": float(obs), "ppc_mean": float(rep.mean()),
                  "ppc_q025": float(np.quantile(rep, 0.025)), "ppc_q975": float(np.quantile(rep, 0.975)),
                  "p_value": float((rep >= obs).mean())}
    # Group means (school, Mjob) -- compare with EDA
    groups = {}
    for col, levels in (("school", SCHOOL_LEVELS), ("Mjob", MJOB_LEVELS)):
        for lvl in levels:
            m = (df[col] == lvl).values
            rep = yrep[:, m].mean(axis=1)
            groups[f"{col}={lvl}"] = {"observed": float(y[m].mean()), "ppc_mean": float(rep.mean()),
                                      "ppc_q025": float(np.quantile(rep, 0.025)),
                                      "ppc_q975": float(np.quantile(rep, 0.975)), "n": int(m.sum())}
    out["group_means"] = groups
    # Error of the posterior predictive mean as a point prediction
    mu_hat = yrep.mean(axis=0)
    out["rmse_in_sample"] = float(np.sqrt(np.mean((mu_hat - y) ** 2)))
    out["mae_in_sample"] = float(np.mean(np.abs(mu_hat - y)))
    return out


def hdi(draws, prob=HDI_PROB):
    """Highest-density interval of a 1-D sample (narrowest interval holding `prob` mass)."""
    x = np.sort(np.asarray(draws).ravel())
    m = int(np.floor(prob * len(x)))
    widths = x[m:] - x[: len(x) - m]
    i = int(np.argmin(widths))
    return float(x[i]), float(x[i + m])


def loo_summary(loo):
    """Version-tolerant extraction of the LOO estimate."""
    elpd = float(getattr(loo, "elpd", getattr(loo, "elpd_loo", np.nan)))
    se = float(getattr(loo, "se", np.nan))
    p = float(getattr(loo, "p", getattr(loo, "p_loo", np.nan)))
    k = np.asarray(getattr(loo, "pareto_k", []))
    return {"elpd_loo": elpd, "se": se, "p_loo": p, "pareto_k_max": float(k.max()) if k.size else None,
            "n_pareto_k_gt_0.7": int((k > 0.7).sum()) if k.size else None,
            "warning": bool(getattr(loo, "warning", False))}


# --------------------------------------------------------------------------- #
def plot_ppc(ppcs, y, df):
    bins = np.arange(-1, 22, 2)  # 2-point bins: [-1,1), [1,3), ..., [19,21)
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.05), gridspec_kw={"width_ratios": [1, 1, 1.35], "wspace": 0.35})
    obs_hist = np.histogram(y, bins=bins)[0] / len(y)
    centers = 0.5 * (bins[1:] + bins[:-1])
    for ax, (name, color) in zip(axes[:2], zip(ppcs.keys(), [BLUE, ORANGE])):
        yrep = ppcs[name]
        rep_hist = np.stack([np.histogram(r, bins=bins)[0] / len(y) for r in yrep[:1000]])
        lo, hi = np.quantile(rep_hist, [0.025, 0.975], axis=0)
        ax.fill_between(centers, lo, hi, color=color, alpha=0.25, lw=0, label="posterior predictive 95%")
        ax.plot(centers, rep_hist.mean(axis=0), color=color, lw=1.2, label="posterior predictive mean")
        ax.plot(centers, obs_hist, "o-", color=INK, lw=1, ms=3, label="observed")
        ax.set_xlabel("final grade G3 (2-point bins)")
        ax.set_title(f"({'ab'[list(ppcs).index(name)]}) {MODEL_TITLES[name].split(' (')[0]}: posterior predictive", fontsize=8)
        ax.set_ylim(0, 0.30)
        ax.set_xticks([0, 5, 10, 15, 20])
        tidy(ax)
    axes[0].set_ylabel("share of students")
    axes[0].legend(loc="upper left", fontsize=6)

    # Group means: observed vs posterior predictive intervals (both models)
    ax = axes[2]
    labels, xs = [], []
    k = 0
    for col, levels in (("school", SCHOOL_LEVELS), ("Mjob", MJOB_LEVELS)):
        for lvl in levels:
            m = (df[col] == lvl).values
            for j, (name, color) in enumerate(zip(ppcs.keys(), [BLUE, ORANGE])):
                rep = ppcs[name][:, m].mean(axis=1)
                lo, hi = np.quantile(rep, [0.025, 0.975])
                off = -0.18 if j == 0 else 0.18
                ax.plot([k + off, k + off], [lo, hi], color=color, lw=1.6, solid_capstyle="round")
                ax.plot(k + off, rep.mean(), "o", color=color, ms=3)
            ax.plot(k, y[m].mean(), "_", color=INK, ms=10, mew=1.5)
            labels.append(f"{lvl}" if col == "school" else lvl.replace("at_home", "home"))
            k += 1
    ax.axvline(1.5, color=INK_2, lw=0.5, ls=":")
    ax.set_xticks(range(k), labels, rotation=30, ha="right")
    ax.set_ylabel("mean G3 in group")
    ax.set_title("(c) group means: observed vs predictive 95%", fontsize=8)
    ax.text(0.5, 13.2, "school", fontsize=6.5, color=INK_2, ha="center")
    ax.text(4, 13.2, "mother's job", fontsize=6.5, color=INK_2, ha="center")
    ax.set_ylim(7, 13.8)
    tidy(ax)
    fig.savefig(OUT_DIR / "fig_ppc.pdf")
    fig.savefig(OUT_DIR / "fig_ppc.png")


def plot_posterior(tables):
    t1, t2 = tables["M1_pooled"], tables["M2_hier"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.1), gridspec_kw={"width_ratios": [1.15, 1], "wspace": 0.5})

    # (a) coefficients, both models
    ax = axes[0]
    labels = [f"beta[{FEATURE_LABELS[f]}]" for f in FEATURES]
    ys = np.arange(len(labels))[::-1]
    for j, (t, color, nm) in enumerate(((t1, BLUE, "Model 1"), (t2, ORANGE, "Model 2"))):
        sub = t.set_index("parameter").loc[labels]
        off = 0.17 if j == 0 else -0.17
        ax.hlines(ys + off, sub["hdi_low"], sub["hdi_high"], color=color, lw=1.6)
        ax.plot(sub["mean"], ys + off, "o", color=color, ms=3.5, label=nm)
    ax.axvline(0, color=INK_2, lw=0.6)
    ax.set_yticks(ys, [FEATURE_LABELS[f] for f in FEATURES])
    ax.set_xlabel("effect on G3 (grade points per SD; yes vs no for 'higher')")
    ax.set_title("(a) coefficients: posterior mean and 95% HDI", fontsize=8)
    ax.legend(loc="lower left", fontsize=6.5)
    tidy(ax, xgrid=True)

    # (b) group-level effects of model 2
    ax = axes[1]
    labels = ([f"a_school[{s}]" for s in SCHOOL_LEVELS] + [f"a_mjob[{m}]" for m in MJOB_LEVELS]
              + ["sigma_school", "sigma_mjob"])
    sub = t2.set_index("parameter").loc[labels]
    ys = np.arange(len(labels))[::-1]
    colors = [AQUA] * 2 + [ORANGE] * 5 + [INK_2] * 2
    for yv, (_, r), c in zip(ys, sub.iterrows(), colors):
        ax.hlines(yv, r["hdi_low"], r["hdi_high"], color=c, lw=1.6)
        ax.plot(r["mean"], yv, "o", color=c, ms=3.5)
    ax.axvline(0, color=INK_2, lw=0.6)
    ax.set_yticks(ys, [l.replace("a_school[", "school ").replace("a_mjob[", "Mjob ").replace("]", "")
                       .replace("at_home", "home") for l in labels])
    ax.set_xlabel("grade points")
    ax.set_title("(b) Model 2 varying intercepts and group scales", fontsize=8)
    tidy(ax, xgrid=True)
    fig.savefig(OUT_DIR / "fig_posterior.pdf")
    fig.savefig(OUT_DIR / "fig_posterior.png")


# --------------------------------------------------------------------------- #
def main() -> None:
    apply_style()
    df = load_data()
    X, school, mjob, y, means, sds = get_arrays(df)
    y_np = np.asarray(y)
    n = len(df)
    key = random.PRNGKey(SEED)

    idatas, tables, ppcs, diags, loos = {}, {}, {}, {}, {}
    for name, model in MODELS.items():
        key, k_fit, k_ppc = random.split(key, 3)
        mcmc = fit_model(name, model, X, school, mjob, y, k_fit)
        diags[name] = diagnostics(mcmc)
        print(f"[{name}] max R-hat = {diags[name]['r_hat_max']:.3f}, min ESS = {diags[name]['ess_min']:.0f}, "
              f"divergences = {diags[name]['divergences']}")
        ppc = Predictive(model, posterior_samples=mcmc.get_samples())(k_ppc, X, school, mjob, y=None)
        ppc = {"G3": ppc["G3"]}
        ppcs[name] = np.asarray(ppc["G3"])
        idatas[name] = to_idata(name, mcmc, ppc, n)
        tables[name] = param_table(name, mcmc, means, sds)
        loo = az.loo(idatas[name], var_name="G3")
        loos[name] = loo_summary(loo)
        print(f"[{name}] LOO: {loos[name]}")

    # Tables and JSON outputs
    pd.concat(tables.values()).to_csv(OUT_DIR / "posterior_summary.csv", index=False)
    (OUT_DIR / "diagnostics.json").write_text(json.dumps(diags, indent=2))
    stats = {name: ppc_stats(name, ppcs[name], y_np, df) for name in MODELS}
    (OUT_DIR / "ppc_stats.json").write_text(json.dumps(stats, indent=2))

    # Model comparison
    cmp = az.compare({"M1_pooled": idatas["M1_pooled"], "M2_hier": idatas["M2_hier"]}, var_name="G3")
    if not hasattr(cmp, "to_csv"):
        cmp = cmp.to_dataframe()
    cmp.to_csv(OUT_DIR / "loo_compare.csv")
    print(cmp.to_string())
    (OUT_DIR / "loo_results.json").write_text(json.dumps(loos, indent=2))

    plot_ppc(ppcs, y_np, df)
    plot_posterior(tables)
    print(pd.concat(tables.values()).round(3).to_string())
    print("Saved outputs to", OUT_DIR)


if __name__ == "__main__":
    main()
