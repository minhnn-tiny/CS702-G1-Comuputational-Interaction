"""Problem 3, Q1 -- Rasch model and multi-armed bandits (epsilon-greedy, Thompson sampling).

Q1.a  ``rasch(beta, delta)`` returns 1 (success) with probability
      sigma(beta - delta) = exp(beta - delta) / (1 + exp(beta - delta)), else 0.
Q1.b  Two bandit algorithms over three team members (arms).
Q1.c  Simulation over T = 1000 trials for several (beta_1, beta_2, beta_3, delta)
      settings, averaged over many independent runs; cumulative regret against
      the oracle that always picks the most able member.

Outputs: outputs/q1_rasch_test.csv, outputs/q1_results.json, outputs/fig_q1_regret.pdf
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.plotstyle import AQUA, BLUE, INK_2, ORANGE, apply_style, tidy  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent / "outputs"
OUT_DIR.mkdir(exist_ok=True)

T = 1000          # horizon
N_RUNS = 200      # independent simulation runs per setting (for smooth averages)
SEED = 702


# --------------------------------------------------------------------------- #
# Q1.a  Rasch model
# --------------------------------------------------------------------------- #
def rasch_probability(beta: float, delta: float) -> float:
    """P(X=1) under the Rasch model for dichotomous outcomes."""
    z = beta - delta
    return float(np.exp(z) / (1.0 + np.exp(z)))


def rasch(beta: float, delta: float, rng: np.random.Generator | None = None) -> int:
    """Sample one task outcome: 1 (completed) or 0 (not completed)."""
    rng = np.random.default_rng() if rng is None else rng
    return int(rng.random() < rasch_probability(beta, delta))


def test_rasch(rng: np.random.Generator, n: int = 1000):
    pairs = [(0.9, 0.1), (0.5, 0.5), (0.1, 0.9), (1.0, 0.0), (0.0, 1.0)]
    rows = []
    for beta, delta in pairs:
        draws = np.array([rasch(beta, delta, rng) for _ in range(n)])
        k = int(draws.sum())
        p = rasch_probability(beta, delta)
        rows.append({"beta": beta, "delta": delta, "beta_minus_delta": round(beta - delta, 2),
                     "theoretical_p": round(p, 4), "successes": k, "failures": n - k,
                     "empirical_p": k / n, "se": round(np.sqrt(p * (1 - p) / n), 4)})
    return rows


# --------------------------------------------------------------------------- #
# Q1.b  Bandit algorithms
# --------------------------------------------------------------------------- #
class EpsilonGreedy:
    """Sample-mean estimates; explore uniformly with probability eps, otherwise exploit."""

    def __init__(self, n_arms: int, eps: float = 0.1, rng=None):
        self.eps, self.rng = eps, rng
        self.counts = np.zeros(n_arms)
        self.values = np.zeros(n_arms)  # running mean reward per arm

    def select(self) -> int:
        if self.rng.random() < self.eps:
            return int(self.rng.integers(len(self.counts)))
        best = np.flatnonzero(self.values == self.values.max())  # random tie-break
        return int(self.rng.choice(best))

    def update(self, arm: int, reward: float) -> None:
        self.counts[arm] += 1
        self.values[arm] += (reward - self.values[arm]) / self.counts[arm]  # incremental mean


class ThompsonSampling:
    """Beta(a0, b0) prior on each arm's success probability; Bernoulli rewards."""

    def __init__(self, n_arms: int, a0: float = 1.0, b0: float = 1.0, rng=None):
        self.rng = rng
        self.alpha = np.full(n_arms, a0, dtype=float)
        self.beta = np.full(n_arms, b0, dtype=float)

    def select(self) -> int:
        theta = self.rng.beta(self.alpha, self.beta)  # one posterior draw per arm
        return int(np.argmax(theta))

    def update(self, arm: int, reward: float) -> None:
        self.alpha[arm] += reward
        self.beta[arm] += 1 - reward


# --------------------------------------------------------------------------- #
# Q1.c  Simulation
# --------------------------------------------------------------------------- #
SETTINGS = {
    "A: well separated (beta=0.9,0.5,0.1; delta=0.5)": dict(betas=(0.9, 0.5, 0.1), delta=0.5),
    "B: close abilities (beta=0.6,0.5,0.4; delta=0.5)": dict(betas=(0.6, 0.5, 0.4), delta=0.5),
    "C: hard task, one expert (beta=1.0,0.2,0.0; delta=0.9)": dict(betas=(1.0, 0.2, 0.0), delta=0.9),
}
ALGORITHMS = {
    "epsilon-greedy (eps=0.1)": lambda rng: EpsilonGreedy(3, eps=0.1, rng=rng),
    "epsilon-greedy (eps=0.02)": lambda rng: EpsilonGreedy(3, eps=0.02, rng=rng),
    "Thompson sampling (Beta(1,1))": lambda rng: ThompsonSampling(3, rng=rng),
}


def run_bandit(make_agent, probs: np.ndarray, rng: np.random.Generator, betas, delta):
    agent = make_agent(rng)
    p_star = probs.max()
    regret = np.empty(T)
    rewards = np.empty(T)
    for t in range(T):
        arm = agent.select()
        r = rasch(betas[arm], delta, rng)
        agent.update(arm, r)
        rewards[t] = r
        regret[t] = p_star - probs[arm]  # expected (pseudo-)regret of the pull
    return np.cumsum(regret), np.cumsum(rewards)


def main() -> None:
    apply_style()
    rng = np.random.default_rng(SEED)

    # Q1.a
    rasch_rows = test_rasch(rng)
    import csv

    with open(OUT_DIR / "q1_rasch_test.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rasch_rows[0].keys())
        w.writeheader()
        w.writerows(rasch_rows)
    print("Rasch test:")
    for r in rasch_rows:
        print(r)

    # Q1.c
    results = {}
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.0), sharey=False)
    colors = {list(ALGORITHMS)[0]: BLUE, list(ALGORITHMS)[1]: AQUA, list(ALGORITHMS)[2]: ORANGE}
    for ax, (sname, cfg) in zip(axes, SETTINGS.items()):
        betas, delta = cfg["betas"], cfg["delta"]
        probs = np.array([rasch_probability(b, delta) for b in betas])
        res = {"betas": betas, "delta": delta, "success_probs": probs.round(4).tolist(),
               "best_arm": int(np.argmax(probs)), "gap_best_second": float(np.sort(probs)[-1] - np.sort(probs)[-2]),
               "oracle_expected_reward": float(T * probs.max()), "algorithms": {}}
        oracle_rewards = np.array([np.cumsum([rasch(betas[np.argmax(probs)], delta, rng) for _ in range(T)])[-1]
                                   for _ in range(N_RUNS)])
        res["oracle_mean_cumulative_reward"] = float(oracle_rewards.mean())
        for aname, make in ALGORITHMS.items():
            regs, rews = zip(*(run_bandit(make, probs, rng, betas, delta) for _ in range(N_RUNS)))
            regs, rews = np.array(regs), np.array(rews)
            mean_reg = regs.mean(axis=0)
            lo, hi = np.quantile(regs, [0.1, 0.9], axis=0)
            ax.fill_between(np.arange(1, T + 1), lo, hi, color=colors[aname], alpha=0.15, lw=0)
            ax.plot(np.arange(1, T + 1), mean_reg, color=colors[aname], label=aname)
            res["algorithms"][aname] = {
                "final_regret_mean": float(mean_reg[-1]), "final_regret_q10_q90": [float(lo[-1]), float(hi[-1])],
                "regret_at_200": float(mean_reg[199]), "mean_cumulative_reward": float(rews[:, -1].mean()),
                "reward_gap_to_oracle": float(res["oracle_mean_cumulative_reward"] - rews[:, -1].mean()),
            }
        results[sname] = res
        ax.set_title(sname.split(" (")[0] + "\n" + "p = " + ", ".join(f"{p:.3f}" for p in probs), fontsize=7.5)
        ax.set_xlabel("trial t")
        tidy(ax)
    axes[0].set_ylabel("cumulative regret (expected)")
    axes[0].legend(loc="upper left", fontsize=6)
    fig.savefig(OUT_DIR / "fig_q1_regret.pdf")
    fig.savefig(OUT_DIR / "fig_q1_regret.png")
    (OUT_DIR / "q1_results.json").write_text(json.dumps(results, indent=2))
    for s, r in results.items():
        print(s, "probs", r["success_probs"])
        for a, v in r["algorithms"].items():
            print(f"   {a:<32} final regret {v['final_regret_mean']:6.1f}  reward {v['mean_cumulative_reward']:6.1f} "
                  f"(oracle {r['oracle_mean_cumulative_reward']:.1f})")


if __name__ == "__main__":
    main()
