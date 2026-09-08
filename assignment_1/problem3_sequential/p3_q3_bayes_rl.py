"""Problem 3, Q3 -- Bayesian model-based reinforcement learning for a fatigued worker.

Q3.a  Simulate the fatigue MDP (3 states x 2 actions) for 100 steps under a
      random policy and summarise the collected data.
Q3.b  Learn the MDP parameters from those data with NumPyro:
          theta_{s,a} ~ Dirichlet(1,1,1),  s' ~ Categorical(theta_{s,a})
          mu_{s,work} ~ Normal(0, 2), sigma_{s,work} ~ HalfNormal(2), r ~ Normal(mu, sigma)
      The reward for `rest` is zero by construction (the worker does not attempt
      a task), so E[r | s, rest] = 0 is treated as known: fitting a Normal
      likelihood to observations that are all exactly 0 would make the
      posterior of sigma_{s,rest} degenerate (it collapses to zero and the
      posterior density is unbounded).  The transition model is learned for all
      six (s, a) pairs.
Q3.c  Solve the LP (Bellman constraints) with the posterior-mean parameters and
      report pi*(s), V*(s); compare with the LP solved on the true parameters.

Outputs: outputs/q3_trajectory.csv, outputs/q3_data_summary.json, outputs/q3_posterior.json,
         outputs/q3_policy.json, outputs/fig_q3.pdf
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpyro

numpyro.set_host_device_count(4)

import jax.numpy as jnp  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import numpyro.distributions as dist  # noqa: E402
import pandas as pd  # noqa: E402
from jax import random  # noqa: E402
from numpyro.diagnostics import summary as numpyro_summary  # noqa: E402
from numpyro.infer import MCMC, NUTS  # noqa: E402
from pyomo.environ import ConcreteModel, ConstraintList, Objective, Reals, SolverFactory, Var, minimize, value  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.plotstyle import AQUA, BLUE, INK, INK_2, ORANGE, apply_style, tidy  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent / "outputs"
OUT_DIR.mkdir(exist_ok=True)

STATE_NAMES = ["fresh", "tired", "exhausted"]
ACTION_NAMES = ["rest", "work"]
# TRUE_P[s, a, s'] -- the transition table of the assignment
TRUE_P = np.array([
    [[0.9, 0.1, 0.0], [0.3, 0.6, 0.1]],
    [[0.6, 0.4, 0.0], [0.0, 0.4, 0.6]],
    [[0.2, 0.7, 0.1], [0.0, 0.1, 0.9]],
])
TRUE_MU_WORK = np.array([1.0, 0.5, -0.5])
TRUE_SIGMA_R = 0.3
N_STEPS = 100
SEED = 704
GAMMAS = [0.9, 0.95, 0.99]


# --------------------------------------------------------------------------- #
# Q3.a  simulator and data collection
# --------------------------------------------------------------------------- #
def mdp_step(s: int, a: int, rng: np.random.Generator):
    s_next = int(rng.choice(3, p=TRUE_P[s, a]))
    r = 0.0 if a == 0 else float(rng.normal(TRUE_MU_WORK[s], TRUE_SIGMA_R))
    return s_next, r


def collect(rng: np.random.Generator, n_steps: int = N_STEPS, s0: int = 0) -> pd.DataFrame:
    rows, s = [], s0
    for t in range(n_steps):
        a = int(rng.random() < 0.5)  # random policy: 50% work, 50% rest
        s_next, r = mdp_step(s, a, rng)
        rows.append({"t": t, "s": s, "a": a, "r": r, "s_next": s_next})
        s = s_next
    return pd.DataFrame(rows)


def summarise(df: pd.DataFrame) -> dict:
    counts = df.groupby(["s", "a"]).size().reindex(pd.MultiIndex.from_product([range(3), range(2)]), fill_value=0)
    trans = np.zeros((3, 2, 3), dtype=int)
    for (s, a, sn), c in df.groupby(["s", "a", "s_next"]).size().items():
        trans[s, a, sn] = c
    rew = df[df.a == 1].groupby("s")["r"].agg(["count", "mean", "std", "min", "max"])
    return {
        "n_steps": int(len(df)),
        "state_visits": df["s"].value_counts().reindex(range(3), fill_value=0).to_dict(),
        "state_action_counts": {f"{STATE_NAMES[s]}/{ACTION_NAMES[a]}": int(c) for (s, a), c in counts.items()},
        "transition_counts": {f"{STATE_NAMES[s]}/{ACTION_NAMES[a]}": trans[s, a].tolist() for s in range(3) for a in range(2)},
        "work_reward_stats": {STATE_NAMES[s]: {k: (float(v) if pd.notna(v) else None) for k, v in row.items()}
                              for s, row in rew.to_dict("index").items()},
        "reward_overall": {"mean": float(df.r.mean()), "sd": float(df.r.std()), "total": float(df.r.sum()),
                           "share_zero_rest": float((df.a == 0).mean())},
    }


# --------------------------------------------------------------------------- #
# Q3.b  Bayesian inference of the MDP parameters
# --------------------------------------------------------------------------- #
def mdp_model(sa_idx, s_next, work_state=None, r_work=None):
    with numpyro.plate("sa_pairs", 6):
        theta = numpyro.sample("theta", dist.Dirichlet(jnp.ones(3)))  # (6, 3): rows = (s, a)
    with numpyro.plate("transitions", len(sa_idx)):
        numpyro.sample("s_next", dist.Categorical(probs=theta[sa_idx]), obs=s_next)
    with numpyro.plate("states", 3):
        mu = numpyro.sample("mu_work", dist.Normal(0.0, 2.0))
        sigma = numpyro.sample("sigma_work", dist.HalfNormal(2.0))
    with numpyro.plate("work_rewards", len(work_state)):
        numpyro.sample("r", dist.Normal(mu[work_state], sigma[work_state]), obs=r_work)


def infer(df: pd.DataFrame, key):
    sa_idx = jnp.asarray((df.s * 2 + df.a).values)
    s_next = jnp.asarray(df.s_next.values)
    work = df[df.a == 1]
    kernel = NUTS(mdp_model, target_accept_prob=0.9)
    mcmc = MCMC(kernel, num_warmup=1000, num_samples=1500, num_chains=4, progress_bar=False)
    mcmc.run(key, sa_idx, s_next, jnp.asarray(work.s.values), jnp.asarray(work.r.values, dtype=jnp.float32))
    return mcmc


def hdi(x, prob=0.95):
    x = np.sort(np.asarray(x).ravel())
    m = int(np.floor(prob * len(x)))
    w = x[m:] - x[: len(x) - m]
    i = int(np.argmin(w))
    return float(x[i]), float(x[i + m])


def posterior_summary(mcmc, df):
    s = mcmc.get_samples()
    theta = np.asarray(s["theta"])  # (S, 6, 3)
    mu = np.asarray(s["mu_work"])  # (S, 3)
    sigma = np.asarray(s["sigma_work"])
    diag = numpyro_summary(mcmc.get_samples(group_by_chain=True), prob=0.95, group_by_chain=True)
    rhat = max(float(np.max(v["r_hat"])) for v in diag.values())
    ess = min(float(np.min(v["n_eff"])) for v in diag.values())
    counts = np.zeros((3, 2, 3))
    for (st, a, sn), c in df.groupby(["s", "a", "s_next"]).size().items():
        counts[st, a, sn] = c
    trans_rows = []
    for st in range(3):
        for a in range(2):
            k = st * 2 + a
            n_sa = counts[st, a].sum()
            for sn in range(3):
                lo, hi = hdi(theta[:, k, sn])
                trans_rows.append({
                    "s": STATE_NAMES[st], "a": ACTION_NAMES[a], "s_next": STATE_NAMES[sn],
                    "true": float(TRUE_P[st, a, sn]), "posterior_mean": float(theta[:, k, sn].mean()),
                    "hdi_low": lo, "hdi_high": hi, "n_visits_sa": int(n_sa), "count": int(counts[st, a, sn]),
                    "conjugate_posterior_mean": float((1 + counts[st, a, sn]) / (3 + n_sa)),
                })
    reward_rows = []
    for st in range(3):
        lo, hi = hdi(mu[:, st])
        slo, shi = hdi(sigma[:, st])
        reward_rows.append({"s": STATE_NAMES[st], "a": "work", "true_mu": float(TRUE_MU_WORK[st]),
                            "posterior_mean_mu": float(mu[:, st].mean()), "mu_hdi_low": lo, "mu_hdi_high": hi,
                            "true_sigma": TRUE_SIGMA_R, "posterior_mean_sigma": float(sigma[:, st].mean()),
                            "sigma_hdi_low": slo, "sigma_hdi_high": shi,
                            "n_obs": int(((df.s == st) & (df.a == 1)).sum())})
        reward_rows.append({"s": STATE_NAMES[st], "a": "rest", "true_mu": 0.0, "posterior_mean_mu": 0.0,
                            "note": "known: no task attempted, reward is exactly 0"})
    tr = pd.DataFrame(trans_rows)
    return {
        "diagnostics": {"r_hat_max": rhat, "ess_min": ess,
                        "divergences": int(np.sum(np.asarray(mcmc.get_extra_fields()["diverging"])))},
        "transitions": trans_rows,
        "rewards": reward_rows,
        "transition_mae": float(np.abs(tr.true - tr.posterior_mean).mean()),
        "transition_max_abs_error": float(np.abs(tr.true - tr.posterior_mean).max()),
        "reward_mu_mae": float(np.mean([abs(r["true_mu"] - r["posterior_mean_mu"]) for r in reward_rows if r["a"] == "work"])),
        "P_hat": theta.mean(axis=0).reshape(3, 2, 3).tolist(),
        "mu_hat": mu.mean(axis=0).tolist(),
        "sigma_hat": sigma.mean(axis=0).tolist(),
    }, theta.mean(axis=0).reshape(3, 2, 3), mu.mean(axis=0)


# --------------------------------------------------------------------------- #
# Q3.c  Policy optimisation with linear programming
# --------------------------------------------------------------------------- #
def solve_lp(P: np.ndarray, mu_work: np.ndarray, gamma: float):
    """min sum_s v(s)  s.t.  v(s) >= R(s,a) + gamma sum_s' P(s'|s,a) v(s')  for all s, a."""
    R = np.zeros((3, 2))
    R[:, 1] = mu_work
    m = ConcreteModel()
    m.v = Var(range(3), domain=Reals)
    m.obj = Objective(expr=sum(m.v[s] for s in range(3)), sense=minimize)
    m.c = ConstraintList()
    for s in range(3):
        for a in range(2):
            m.c.add(m.v[s] >= R[s, a] + gamma * sum(P[s, a, sn] * m.v[sn] for sn in range(3)))
    solver = SolverFactory("appsi_highs")
    if not solver.available(exception_flag=False):
        solver = SolverFactory("highs")
    solver.solve(m)
    V = np.array([value(m.v[s]) for s in range(3)])
    Q = R + gamma * np.einsum("sat,t->sa", P, V)
    policy = Q.argmax(axis=1)
    return V, Q, policy


def evaluate_policy(P: np.ndarray, mu_work: np.ndarray, policy: np.ndarray, gamma: float) -> np.ndarray:
    """Exact value of a deterministic policy on the MDP (P, mu): V = (I - gamma P_pi)^-1 R_pi."""
    R = np.array([mu_work[s] if policy[s] == 1 else 0.0 for s in range(3)])
    Ppi = np.array([P[s, policy[s]] for s in range(3)])
    return np.linalg.solve(np.eye(3) - gamma * Ppi, R)


# --------------------------------------------------------------------------- #
def plot(df, post, P_hat, mu_hat):
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 2.05), gridspec_kw={"width_ratios": [0.8, 1.7, 0.8], "wspace": 0.38})

    # (a) state-action visits
    ax = axes[0]
    sa = df.groupby(["s", "a"]).size().reindex(pd.MultiIndex.from_product([range(3), range(2)]), fill_value=0)
    xs = np.arange(3)
    ax.bar(xs - 0.19, [sa[(s, 0)] for s in range(3)], width=0.36, color=AQUA, label="rest")
    ax.bar(xs + 0.19, [sa[(s, 1)] for s in range(3)], width=0.36, color=BLUE, label="work")
    ax.set_xticks(xs, STATE_NAMES)
    ax.set_ylabel("visits in 100 steps")
    ax.set_title("(a) state-action visits", fontsize=8)
    ax.set_ylim(0, 27)
    ax.legend(fontsize=6.5, loc="upper right", ncol=2)
    tidy(ax)

    # (b) transition probabilities: true vs posterior mean with 95% HDI
    ax = axes[1]
    tr = pd.DataFrame(post["transitions"])
    labels, k = [], 0
    for s in range(3):
        for a in range(2):
            sub = tr[(tr.s == STATE_NAMES[s]) & (tr.a == ACTION_NAMES[a])]
            for j, (_, r) in enumerate(sub.iterrows()):
                x = k * 4 + j
                ax.bar(x - 0.2, r["true"], width=0.4, color=INK_2, alpha=0.5)
                ax.bar(x + 0.2, r["posterior_mean"], width=0.4, color=BLUE)
                ax.plot([x + 0.2, x + 0.2], [r["hdi_low"], r["hdi_high"]], color=INK, lw=0.8)
            labels.append(f"{STATE_NAMES[s][:3]}/{ACTION_NAMES[a]}\n(n={int(sub.n_visits_sa.iloc[0])})")
            k += 1
    ax.set_xticks([k * 4 + 1 for k in range(6)], labels, fontsize=6)
    ax.set_ylabel("P(s' | s, a)")
    ax.set_ylim(0, 1.05)
    ax.set_title("(b) P(s' | s, a): true (grey) vs posterior mean, 95% HDI (blue)", fontsize=7.5)
    tidy(ax)

    # (c) reward means for work
    ax = axes[2]
    rw = [r for r in post["rewards"] if r["a"] == "work"]
    xs = np.arange(3)
    ax.bar(xs - 0.19, [r["true_mu"] for r in rw], width=0.36, color=INK_2, alpha=0.5, label="true")
    ax.bar(xs + 0.19, [r["posterior_mean_mu"] for r in rw], width=0.36, color=ORANGE, label="posterior")
    for x, r in zip(xs, rw):
        ax.plot([x + 0.19, x + 0.19], [r["mu_hdi_low"], r["mu_hdi_high"]], color=INK, lw=0.8)
    ax.axhline(0, color=INK_2, lw=0.6)
    ax.set_xticks(xs, STATE_NAMES)
    ax.set_ylabel("E[r | s, work]")
    ax.set_title("(c) E[r | s, work]", fontsize=8)
    ax.set_ylim(-0.8, 1.45)
    ax.legend(fontsize=6.5, loc="upper right")
    tidy(ax)
    fig.savefig(OUT_DIR / "fig_q3.pdf")
    fig.savefig(OUT_DIR / "fig_q3.png")


def main() -> None:
    apply_style()
    rng = np.random.default_rng(SEED)
    df = collect(rng)
    df.to_csv(OUT_DIR / "q3_trajectory.csv", index=False)
    data_summary = summarise(df)
    (OUT_DIR / "q3_data_summary.json").write_text(json.dumps(data_summary, indent=2))
    print(json.dumps(data_summary, indent=2))

    mcmc = infer(df, random.PRNGKey(SEED))
    post, P_hat, mu_hat = posterior_summary(mcmc, df)
    (OUT_DIR / "q3_posterior.json").write_text(json.dumps(post, indent=2))
    print("diagnostics:", post["diagnostics"])
    print(pd.DataFrame(post["transitions"]).round(3).to_string(index=False))
    print(pd.DataFrame(post["rewards"]).round(3).to_string(index=False))
    print(f"transition MAE = {post['transition_mae']:.3f}, max = {post['transition_max_abs_error']:.3f}, "
          f"reward MAE = {post['reward_mu_mae']:.3f}")

    policies = {}
    for gamma in GAMMAS:
        V_hat, Q_hat, pi_hat = solve_lp(P_hat, mu_hat, gamma)
        V_true, Q_true, pi_true = solve_lp(TRUE_P, TRUE_MU_WORK, gamma)
        V_pihat_on_true = evaluate_policy(TRUE_P, TRUE_MU_WORK, pi_hat, gamma)
        policies[f"gamma={gamma}"] = {
            "learned_model": {"policy": [ACTION_NAMES[a] for a in pi_hat], "V": V_hat.round(4).tolist(),
                              "Q": Q_hat.round(4).tolist()},
            "true_model": {"policy": [ACTION_NAMES[a] for a in pi_true], "V": V_true.round(4).tolist(),
                           "Q": Q_true.round(4).tolist()},
            "value_of_learned_policy_on_true_mdp": V_pihat_on_true.round(4).tolist(),
            "policies_agree": bool(np.all(pi_hat == pi_true)),
        }
        print(f"gamma={gamma}: learned-model policy {[ACTION_NAMES[a] for a in pi_hat]} V={V_hat.round(3)} | "
              f"true-model policy {[ACTION_NAMES[a] for a in pi_true]} V={V_true.round(3)} | "
              f"learned policy on true MDP V={V_pihat_on_true.round(3)}")
    (OUT_DIR / "q3_policy.json").write_text(json.dumps(policies, indent=2))
    plot(df, post, P_hat, mu_hat)


if __name__ == "__main__":
    main()
