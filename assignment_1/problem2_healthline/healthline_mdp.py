"""Problem 2 -- the HealthLine MDP as plain Python data (single source of truth).

The same definition is used to draw the diagram, to analyse PRISM simulation
traces, to cross-check PRISM's model-checking results, to build the linear
program, and to derive the DTMC induced by the optimal policy.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / "outputs"
OUT_DIR.mkdir(exist_ok=True)

STATE_NAMES = {
    0: "initial",
    1: "acute_track",
    2: "general_track",
    3: "admin_track",
    4: "triage_complete (warning signs)",
    5: "triage_complete (no warning signs)",
    6: "information_delivered",
    7: "resolved",
    8: "escalated_nurse",
    9: "escalated_admin",
    10: "emergency",
    11: "abandoned",
}
STATES = list(range(12))
TERMINAL = [7, 8, 9, 10, 11]
NON_TERMINAL = [s for s in STATES if s not in TERMINAL]
INITIAL = 0

# (state, action) -> {next_state: probability}
TRANSITIONS = {
    (0, "classify"): {1: 0.25, 2: 0.45, 3: 0.20, 11: 0.10},
    (1, "quick_screen"): {4: 0.15, 5: 0.65, 11: 0.20},
    (1, "thorough_screen"): {4: 0.25, 5: 0.50, 11: 0.25},
    (2, "brief_response"): {6: 0.75, 11: 0.25},
    (2, "detailed_response"): {6: 0.85, 11: 0.15},
    (3, "auto_process"): {7: 0.60, 9: 0.25, 11: 0.15},
    (3, "transfer_to_admin"): {9: 0.90, 11: 0.10},
    (4, "emergency_referral"): {10: 1.00},
    (4, "offer_nurse"): {8: 0.85, 10: 0.15},
    (5, "offer_nurse"): {8: 1.00},
    (6, "check_satisfaction"): {7: 0.55, 8: 0.35, 11: 0.10},
}
ACTIONS = {s: [a for (ss, a) in TRANSITIONS if ss == s] for s in NON_TERMINAL}

# Terminal-state rewards (received once, on entering the terminal state)
REWARDS = {7: 10.0, 8: 6.0, 9: 5.0, 10: 12.0, 11: 0.0}


def reward(next_state: int) -> float:
    return REWARDS.get(next_state, 0.0)


def q_values(V: dict, gamma: float = 1.0) -> dict:
    """Q(s,a) = sum_s' p(s'|s,a) [ r(s') + gamma V(s') ] for a given value function."""
    return {(s, a): sum(p * (reward(sn) + gamma * V[sn]) for sn, p in P.items()) for (s, a), P in TRANSITIONS.items()}


def value_iteration(mode: str = "max", gamma: float = 1.0, iters: int = 200) -> tuple[dict, dict]:
    """Exact optimal (mode='max') or worst-case (mode='min') values by value iteration."""
    V = {s: 0.0 for s in STATES}
    agg = max if mode == "max" else min
    for _ in range(iters):
        Q = q_values(V, gamma)
        V = {s: (agg(Q[(s, a)] for a in ACTIONS[s]) if s in ACTIONS else 0.0) for s in STATES}
    Q = q_values(V, gamma)
    policy = {s: agg(ACTIONS[s], key=lambda a: Q[(s, a)]) for s in NON_TERMINAL}
    return V, policy


def reach_probability(target: set[int], mode: str = "max", iters: int = 200) -> dict:
    """Max/min probability of eventually reaching a set of states (value iteration)."""
    p = {s: (1.0 if s in target else 0.0) for s in STATES}
    agg = max if mode == "max" else min
    for _ in range(iters):
        new = dict(p)
        for s in NON_TERMINAL:
            if s in target:
                continue
            new[s] = agg(sum(pr * p[sn] for sn, pr in TRANSITIONS[(s, a)].items()) for a in ACTIONS[s])
        p = new
    return p


def induced_dtmc(policy: dict) -> dict:
    """Transition function of the DTMC obtained by fixing a deterministic policy."""
    P = {s: dict(TRANSITIONS[(s, policy[s])]) for s in NON_TERMINAL}
    for t in TERMINAL:
        P[t] = {t: 1.0}
    return P


def dtmc_absorption(P: dict, start: int = INITIAL, iters: int = 200) -> dict:
    """Probability of ending in each terminal state, starting from `start`."""
    out = {}
    for t in TERMINAL:
        p = {s: (1.0 if s == t else 0.0) for s in STATES}
        for _ in range(iters):
            p = {s: (p[s] if s in TERMINAL else sum(pr * p[sn] for sn, pr in P[s].items())) for s in STATES}
        out[t] = p[start]
    return out


def random_policy_outcomes() -> dict:
    """Outcome distribution and expected reward when actions are chosen uniformly at random
    (this is how PRISM's simulator resolves non-determinism)."""
    P = {}
    for s in NON_TERMINAL:
        acts = ACTIONS[s]
        P[s] = {}
        for a in acts:
            for sn, pr in TRANSITIONS[(s, a)].items():
                P[s][sn] = P[s].get(sn, 0.0) + pr / len(acts)
    for t in TERMINAL:
        P[t] = {t: 1.0}
    absorb = dtmc_absorption(P)
    return {"outcome_probs": absorb, "expected_reward": sum(absorb[t] * REWARDS[t] for t in TERMINAL)}


# --------------------------------------------------------------------------- #
# PRISM helpers
# --------------------------------------------------------------------------- #
def find_prism() -> str:
    """Locate the PRISM executable: $PRISM_HOME/bin/prism, `prism` on PATH, or ../../tools/prism-*/bin/prism."""
    home = os.environ.get("PRISM_HOME")
    if home and (Path(home) / "bin" / "prism").exists():
        return str(Path(home) / "bin" / "prism")
    on_path = shutil.which("prism")
    if on_path:
        return on_path
    for cand in sorted((HERE.parents[1] / "tools").glob("prism-*/bin/prism")):
        return str(cand)
    raise FileNotFoundError("PRISM not found. Set PRISM_HOME or put `prism` on your PATH.")


def run_prism(args: list[str], timeout: int = 300) -> str:
    cmd = [find_prism(), *args]
    res = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    if res.returncode != 0:
        raise RuntimeError(f"PRISM failed ({res.returncode}):\n{res.stdout}\n{res.stderr}")
    return res.stdout


def parse_results(stdout: str) -> list[tuple[str, float]]:
    """Return [(property, value), ...] from PRISM's console output."""
    out, prop = [], None
    for line in stdout.splitlines():
        if line.startswith("Model checking: "):
            prop = line[len("Model checking: "):].strip()
        elif line.startswith("Result: ") and prop is not None:
            val = line[len("Result: "):].split()[0]
            out.append((prop, float(val)))
            prop = None
    return out
