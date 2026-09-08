"""Problem 2, Q1.c -- forward simulation of the HealthLine MDP with PRISM.

Generates 100 traces with PRISM's discrete-event simulator
(``prism healthline.pm -simpath 20 <file>``; non-deterministic choices are
resolved uniformly at random, and the path stops when the terminal self-loop
is detected) and analyses the outcomes, the abandonment rate, the average
terminal reward and the trace lengths.  The empirical frequencies are
compared with the exact outcome distribution under the uniform-random policy.

Outputs: outputs/prism_traces.csv, outputs/simulation_summary.json, outputs/fig_simulation.pdf
"""

from __future__ import annotations

import json
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common.plotstyle import BLUE, INK, INK_2, ORANGE, apply_style, tidy  # noqa: E402
from healthline_mdp import HERE, OUT_DIR, REWARDS, STATE_NAMES, TERMINAL, random_policy_outcomes, run_prism  # noqa: E402

N_TRACES = 100
MAX_STEPS = 20


def simulate_one(i: int) -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        path_file = Path(tmp) / f"path_{i}.txt"
        run_prism([str(HERE / "healthline.pm"), "-simpath", str(MAX_STEPS), str(path_file)])
        lines = path_file.read_text().strip().splitlines()
    header = lines[0].split()
    ia, istep, istate = header.index("action"), header.index("step"), header.index("s")
    states, actions = [], []
    for row in lines[1:]:
        parts = row.split()
        s = int(parts[istate])
        a = parts[ia].strip("[]")
        if a != "-" and a != "done":
            actions.append(a)
        states.append(s)
        if s in TERMINAL:
            break
    outcome = states[-1]
    return {"trace": i, "states": "->".join(map(str, states)), "actions": ",".join(actions),
            "outcome": outcome, "outcome_name": STATE_NAMES[outcome].split(" (")[0],
            "reward": REWARDS[outcome], "n_transitions": len(states) - 1}


def main() -> None:
    apply_style()
    with ThreadPoolExecutor(max_workers=4) as ex:
        traces = list(ex.map(simulate_one, range(N_TRACES)))
    df = pd.DataFrame(traces)
    df.to_csv(OUT_DIR / "prism_traces.csv", index=False)

    ref = random_policy_outcomes()
    counts = df["outcome"].value_counts().reindex(TERMINAL, fill_value=0)
    n = len(df)
    summary = {
        "n_traces": int(n),
        "outcome_counts": {STATE_NAMES[t]: int(counts[t]) for t in TERMINAL},
        "outcome_share": {STATE_NAMES[t]: float(counts[t] / n) for t in TERMINAL},
        "expected_share_random_policy": {STATE_NAMES[t]: ref["outcome_probs"][t] for t in TERMINAL},
        "abandonment_rate": float((df["outcome"] == 11).mean()),
        "abandonment_rate_ci95": [float(x) for x in binom_ci(int(counts[11]), n)],
        "expected_abandonment_random_policy": ref["outcome_probs"][11],
        "average_reward": float(df["reward"].mean()),
        "reward_sd": float(df["reward"].std()),
        "reward_se": float(df["reward"].std() / np.sqrt(n)),
        "expected_reward_random_policy": ref["expected_reward"],
        "average_transitions": float(df["n_transitions"].mean()),
        "transition_counts": df["n_transitions"].value_counts().sort_index().to_dict(),
        "action_counts": pd.Series([a for acts in df["actions"] for a in acts.split(",") if a]).value_counts().to_dict(),
        "most_common_outcome": STATE_NAMES[int(counts.idxmax())],
    }
    (OUT_DIR / "simulation_summary.json").write_text(json.dumps(summary, indent=2, default=str))

    # ------------------------------------------------------------------ figure
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 1.9), gridspec_kw={"width_ratios": [1.6, 1]})
    ax = axes[0]
    xs = np.arange(len(TERMINAL))
    emp = np.array([counts[t] / n for t in TERMINAL])
    exp = np.array([ref["outcome_probs"][t] for t in TERMINAL])
    err = np.array([binom_ci(int(counts[t]), n) for t in TERMINAL])
    ax.bar(xs - 0.19, emp, width=0.36, color=BLUE, label=f"PRISM simulation ({n} traces)")
    ax.errorbar(xs - 0.19, emp, yerr=[emp - err[:, 0], err[:, 1] - emp], fmt="none", ecolor=INK_2, lw=0.7, capsize=2)
    ax.bar(xs + 0.19, exp, width=0.36, color=ORANGE, label="exact, uniform-random policy")
    for x, e in zip(xs, emp):
        ax.text(x - 0.19, e + 0.02, f"{int(round(e*n))}", ha="center", fontsize=6.5, color=INK)
    ax.set_xticks(xs, [STATE_NAMES[t].replace("escalated_", "esc. ") for t in TERMINAL])
    ax.set_ylabel("share of traces")
    ax.set_ylim(0, max(emp.max(), exp.max()) * 1.3)
    ax.set_title("(a) terminal outcomes of 100 simulated conversations")
    ax.legend(loc="upper right", fontsize=6.5)
    tidy(ax)

    ax = axes[1]
    tc = df["n_transitions"].value_counts().sort_index()
    ax.bar(tc.index, tc.values, color=BLUE, width=0.6)
    ax.set_xlabel("number of transitions per trace")
    ax.set_ylabel("traces")
    ax.set_xticks([1, 2, 3])
    ax.set_title(f"(b) trace length (mean {summary['average_transitions']:.2f})")
    tidy(ax)
    fig.savefig(OUT_DIR / "fig_simulation.pdf")
    fig.savefig(OUT_DIR / "fig_simulation.png")

    print(json.dumps(summary, indent=2, default=str))
    print(df.head(10).to_string(index=False))


def binom_ci(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Wilson score interval."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z**2 / n
    centre = (p + z**2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0.0, centre - half), min(1.0, centre + half))


if __name__ == "__main__":
    main()
