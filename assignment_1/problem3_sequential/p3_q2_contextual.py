"""Problem 3, Q2 -- contextual (combinatorial) bandit for one-to-one task assignment.

Each round a triplet of tasks (types j = 1, 2, 3 with difficulties delta_j) is
allocated to the three team members (one task each).  Member i succeeds on task
type j with probability p_ij = sigma(beta_ij - delta_j) (Rasch model), reward 1
per completed task.

Algorithm (combinatorial Thompson sampling, "CTS"):
    * keep an independent Beta(a_ij, b_ij) posterior for every member-task pair
      (9 pairs), starting from Beta(1, 1);
    * each round draw one sample p~_ij from every posterior and pick the
      assignment (permutation) that maximises the sampled total success
      sum_i p~_{i, sigma(i)}  (all 3! = 6 permutations are enumerated);
    * observe the three outcomes and update the three posteriors that were used.
Sampling from the posteriors makes uncertain pairs occasionally look attractive
(exploration) while well-known good pairs are chosen most of the time
(exploitation).  The learned p_ij map to abilities via beta_ij = logit(p_ij) + delta_j.
A greedy/epsilon-greedy matching baseline is included for comparison.

Outputs: outputs/q2_results.json, outputs/fig_q2_regret.pdf, outputs/fig_q2_learned.pdf
"""

from __future__ import annotations

import itertools
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.plotstyle import AQUA, BLUE, BLUES, INK, INK_2, ORANGE, apply_style, tidy  # noqa: E402

OUT_DIR = Path(__file__).resolve().parent / "outputs"
OUT_DIR.mkdir(exist_ok=True)

T = 1000
N_RUNS = 200
SEED = 703
PERMS = list(itertools.permutations(range(3)))  # sigma[i] = task given to member i


def sigmoid(z):
    return 1.0 / (1.0 + np.exp(-z))


def success_matrix(betas: np.ndarray, deltas: np.ndarray) -> np.ndarray:
    return sigmoid(betas - deltas[None, :])


def best_assignment(P: np.ndarray):
    scores = [sum(P[i, perm[i]] for i in range(3)) for perm in PERMS]
    k = int(np.argmax(scores))
    return PERMS[k], scores[k]


class CombinatorialThompson:
    def __init__(self, rng, a0=1.0, b0=1.0):
        self.rng = rng
        self.a = np.full((3, 3), a0)
        self.b = np.full((3, 3), b0)

    def select(self):
        sample = self.rng.beta(self.a, self.b)
        perm, _ = best_assignment(sample)
        return perm

    def update(self, perm, outcomes):
        for i, j in enumerate(perm):
            self.a[i, j] += outcomes[i]
            self.b[i, j] += 1 - outcomes[i]

    def posterior_mean(self):
        return self.a / (self.a + self.b)


class EpsilonGreedyMatching:
    def __init__(self, rng, eps=0.1):
        self.rng, self.eps = rng, eps
        self.n = np.zeros((3, 3))
        self.mean = np.full((3, 3), 0.5)  # optimistic-neutral initial estimate

    def select(self):
        if self.rng.random() < self.eps:
            return PERMS[self.rng.integers(len(PERMS))]
        perm, _ = best_assignment(self.mean + 1e-9 * self.rng.random((3, 3)))
        return perm

    def update(self, perm, outcomes):
        for i, j in enumerate(perm):
            self.n[i, j] += 1
            self.mean[i, j] += (outcomes[i] - self.mean[i, j]) / self.n[i, j]

    def posterior_mean(self):
        return self.mean


SETTINGS = {
    "A: specialists": dict(
        betas=np.array([[0.9, 0.1, 0.1], [0.1, 0.9, 0.1], [0.1, 0.1, 0.9]]), deltas=np.array([0.5, 0.5, 0.5])),
    "B: generalists": dict(
        betas=np.array([[0.55, 0.50, 0.45], [0.50, 0.55, 0.50], [0.45, 0.50, 0.55]]), deltas=np.array([0.3, 0.5, 0.7])),
    "C: one strong member": dict(
        betas=np.array([[1.0, 0.9, 0.8], [0.3, 0.6, 0.2], [0.2, 0.2, 0.7]]), deltas=np.array([0.4, 0.6, 0.8])),
}
ALGORITHMS = {"combinatorial Thompson sampling": lambda rng: CombinatorialThompson(rng),
              "epsilon-greedy matching (eps=0.1)": lambda rng: EpsilonGreedyMatching(rng, 0.1)}


def run(make_agent, P, rng):
    agent = make_agent(rng)
    perm_star, score_star = best_assignment(P)
    regret, reward = np.empty(T), np.empty(T)
    for t in range(T):
        perm = agent.select()
        probs = np.array([P[i, perm[i]] for i in range(3)])
        outcomes = (rng.random(3) < probs).astype(int)
        agent.update(perm, outcomes)
        reward[t] = outcomes.sum()
        regret[t] = score_star - probs.sum()
    return np.cumsum(regret), np.cumsum(reward), agent.posterior_mean(), perm == perm_star


def main() -> None:
    apply_style()
    rng = np.random.default_rng(SEED)
    results = {}
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.0))
    learned_examples = {}
    for ax, (sname, cfg) in zip(axes, SETTINGS.items()):
        P = success_matrix(cfg["betas"], cfg["deltas"])
        perm_star, score_star = best_assignment(P)
        scores = sorted((sum(P[i, perm[i]] for i in range(3)) for perm in PERMS), reverse=True)
        res = {"betas": cfg["betas"].tolist(), "deltas": cfg["deltas"].tolist(), "P": P.round(3).tolist(),
               "optimal_assignment_member_to_task": [int(j) + 1 for j in perm_star],
               "optimal_expected_reward_per_round": float(score_star),
               "gap_to_second_best_assignment": float(scores[0] - scores[1]),
               "spread_of_P": float(P.max() - P.min()), "algorithms": {}}
        for aname, make, color in zip(ALGORITHMS, ALGORITHMS.values(), [BLUE, ORANGE]):
            out = [run(make, P, rng) for _ in range(N_RUNS)]
            regs = np.array([o[0] for o in out])
            rews = np.array([o[1] for o in out])
            final_opt = np.mean([o[3] for o in out])
            mean_reg = regs.mean(axis=0)
            lo, hi = np.quantile(regs, [0.1, 0.9], axis=0)
            ax.fill_between(np.arange(1, T + 1), lo, hi, color=color, alpha=0.15, lw=0)
            ax.plot(np.arange(1, T + 1), mean_reg, color=color, label=aname)
            res["algorithms"][aname] = {
                "final_regret_mean": float(mean_reg[-1]), "final_regret_q10_q90": [float(lo[-1]), float(hi[-1])],
                "regret_at_200": float(mean_reg[199]),
                "mean_cumulative_reward": float(rews[:, -1].mean()),
                "oracle_cumulative_reward": float(T * score_star),
                "share_runs_ending_on_optimal_assignment": float(final_opt),
                "learned_P_last_run": np.asarray(out[-1][2]).round(3).tolist(),
                "mean_abs_error_P_last_run": float(np.abs(np.asarray(out[-1][2]) - P).mean()),
            }
            if aname.startswith("combinatorial"):
                learned_examples[sname] = (P, np.asarray(out[-1][2]))
        results[sname] = res
        ax.set_title(f"{sname}  (optimal {score_star:.2f}/round)", fontsize=7.5)
        ax.set_xlabel("round t")
        tidy(ax)
    axes[0].set_ylabel("cumulative regret (expected)")
    axes[0].legend(loc="upper left", fontsize=6)
    fig.savefig(OUT_DIR / "fig_q2_regret.pdf")
    fig.savefig(OUT_DIR / "fig_q2_regret.png")

    # learned vs true success matrices (one CTS run per setting)
    fig, axes = plt.subplots(1, 6, figsize=(7.4, 1.5), gridspec_kw={"wspace": 0.45})
    for k, (sname, (P, Phat)) in enumerate(learned_examples.items()):
        for j, (M, title) in enumerate(((P, "true p"), (Phat, "learned (CTS)"))):
            ax = axes[2 * k + j]
            ax.imshow(M, cmap="Blues", vmin=0.25, vmax=0.75)
            for i in range(3):
                for jj in range(3):
                    ax.text(jj, i, f"{M[i, jj]:.2f}", ha="center", va="center", fontsize=6.5,
                            color="white" if M[i, jj] > 0.55 else INK)
            ax.set_xticks(range(3), ["t1", "t2", "t3"])
            ax.set_yticks(range(3), ["m1", "m2", "m3"] if j == 0 else [])
            ax.set_title(f"{sname[:1]}: {title}", fontsize=7)
            ax.grid(False)
    fig.savefig(OUT_DIR / "fig_q2_learned.pdf")
    fig.savefig(OUT_DIR / "fig_q2_learned.png")

    (OUT_DIR / "q2_results.json").write_text(json.dumps(results, indent=2))
    for s, r in results.items():
        print(s, "optimal", r["optimal_assignment_member_to_task"], f"{r['optimal_expected_reward_per_round']:.3f}/round",
              "gap", round(r["gap_to_second_best_assignment"], 3))
        for a, v in r["algorithms"].items():
            print(f"   {a:<36} final regret {v['final_regret_mean']:6.1f}  reward {v['mean_cumulative_reward']:7.1f} "
                  f"(oracle {v['oracle_cumulative_reward']:.0f})  ends optimal {v['share_runs_ending_on_optimal_assignment']:.2f}")


if __name__ == "__main__":
    main()
