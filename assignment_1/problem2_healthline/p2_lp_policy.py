"""Problem 2, Q2 -- optimal policy by linear programming (Pyomo + HiGHS) and the
induced DTMC.

LP (Bellman-constraint formulation, see the lecture note on optimisation):

    minimise   sum_{s in non-terminal} v(s)
    subject to v(s) >= sum_{s'} p(s'|s,a) [ r(s') + gamma v(s') ]   for all s, a
               v(s) = 0                                             for all terminal s

The optimal policy is pi*(s) = argmax_a sum_{s'} p(s'|s,a) [ r(s') + gamma v*(s') ].
Because every episode terminates after at most three transitions, total reward
is well defined without discounting and we use gamma = 1.

Outputs: outputs/lp_policy.json, outputs/lp_policy_table.csv,
         healthline_optimal.pm / healthline_optimal.props (DTMC under pi*),
         outputs/dtmc_check.json (PRISM results for the DTMC).
"""

from __future__ import annotations

import json
import sys

import pandas as pd
from pyomo.environ import ConcreteModel, ConstraintList, Objective, Reals, SolverFactory, Var, maximize, minimize, value

from healthline_mdp import (
    ACTIONS,
    HERE,
    NON_TERMINAL,
    OUT_DIR,
    REWARDS,
    STATE_NAMES,
    STATES,
    TERMINAL,
    TRANSITIONS,
    dtmc_absorption,
    induced_dtmc,
    parse_results,
    q_values,
    reward,
    run_prism,
)

GAMMA = 1.0


def solve_lp(sense=minimize, gamma: float = GAMMA):
    """sense=minimize with v >= Q gives the optimal (max-reward) values;
    sense=maximize with v <= Q gives the worst-case (min-reward) values (cross-check)."""
    m = ConcreteModel()
    m.v = Var(STATES, domain=Reals)
    for t in TERMINAL:
        m.v[t].fix(0.0)
    m.obj = Objective(expr=sum(m.v[s] for s in NON_TERMINAL), sense=sense)
    m.bellman = ConstraintList()
    for (s, a), P in TRANSITIONS.items():
        rhs = sum(p * (reward(sn) + gamma * m.v[sn]) for sn, p in P.items())
        m.bellman.add(m.v[s] >= rhs if sense == minimize else m.v[s] <= rhs)
    solver = SolverFactory("appsi_highs")
    if not solver.available(exception_flag=False):
        solver = SolverFactory("highs")
    res = solver.solve(m)
    V = {s: float(value(m.v[s])) for s in STATES}
    return V, str(res.solver.termination_condition)


def write_dtmc(policy: dict) -> None:
    lines = ["// HealthLine DTMC induced by the LP-optimal policy (Problem 2, Q2.c)",
             "// Run:  prism healthline_optimal.pm healthline_optimal.props", "dtmc", "", "module healthline_dtmc",
             "    s : [0..11] init 0;"]
    for s in NON_TERMINAL:
        a = policy[s]
        terms = " + ".join(f"{p:.2f} : (s'={sn})" for sn, p in TRANSITIONS[(s, a)].items())
        lines.append(f"    [{a}] s={s} -> {terms};")
    lines += ["    [done] s>=7 -> true;", "endmodule", ""]
    for s, name in STATE_NAMES.items():
        lbl = name.split(" (")[0]
        if s in (4, 5):
            lbl = "warning_signs" if s == 4 else "no_warning_signs"
        lines.append(f'label "{lbl}" = (s={s});')
    lines += ['label "terminal" = (s>=7);', "", 'rewards "outcome"']
    lines += [f"    s={t} : {int(r)};" for t, r in REWARDS.items()]
    lines += ["endrewards", ""]
    (HERE / "healthline_optimal.pm").write_text("\n".join(lines))
    props = ['// Reachability probabilities of the DTMC induced by the optimal policy',
             'P=? [ F "resolved" ]', 'P=? [ F "abandoned" ]', 'P=? [ F "escalated_nurse" ]',
             'P=? [ F "escalated_admin" ]', 'P=? [ F "emergency" ]',
             'P=? [ F ("terminal" & !"abandoned") ]', 'R{"outcome"}=? [ I=3 ]', ""]
    (HERE / "healthline_optimal.props").write_text("\n".join(props))


def main() -> None:
    V, status = solve_lp(minimize)
    Q = q_values(V, GAMMA)
    policy = {s: max(ACTIONS[s], key=lambda a: Q[(s, a)]) for s in NON_TERMINAL}
    V_worst, _ = solve_lp(maximize)

    rows = []
    for s in NON_TERMINAL:
        for a in ACTIONS[s]:
            rows.append({"state": f"s{s}", "state_name": STATE_NAMES[s], "action": a, "Q": round(Q[(s, a)], 4),
                         "V": round(V[s], 4), "optimal": a == policy[s], "decision_state": len(ACTIONS[s]) > 1})
    table = pd.DataFrame(rows)
    table.to_csv(OUT_DIR / "lp_policy_table.csv", index=False)

    # DTMC under the optimal policy
    P = induced_dtmc(policy)
    absorb = dtmc_absorption(P)
    write_dtmc(policy)
    prism_out = run_prism([str(HERE / "healthline_optimal.pm"), str(HERE / "healthline_optimal.props")])
    prism_dtmc = parse_results(prism_out)
    (OUT_DIR / "prism_dtmc_log.txt").write_text(prism_out)

    result = {
        "gamma": GAMMA,
        "solver_status": status,
        "V_optimal": V,
        "V_worst_case": V_worst,
        "Q": {f"s{s}|{a}": q for (s, a), q in Q.items()},
        "policy": {f"s{s}": a for s, a in policy.items()},
        "decision_states": {f"s{s}": policy[s] for s in NON_TERMINAL if len(ACTIONS[s]) > 1},
        "expected_total_reward_from_s0": V[0],
        "worst_case_expected_reward_from_s0": V_worst[0],
        "dtmc_outcome_probabilities": {STATE_NAMES[t]: p for t, p in absorb.items()},
        "dtmc_expected_reward": sum(absorb[t] * REWARDS[t] for t in TERMINAL),
        "prism_dtmc_results": prism_dtmc,
    }
    (OUT_DIR / "lp_policy.json").write_text(json.dumps(result, indent=2))
    (OUT_DIR / "dtmc_check.json").write_text(json.dumps(prism_dtmc, indent=2))
    print("LP status:", status)
    print(table.to_string(index=False))
    print("optimal policy:", result["decision_states"])
    print(f"V*(s0) = {V[0]:.4f}   worst-case V(s0) = {V_worst[0]:.4f}")
    print("DTMC outcome probabilities:", {k: round(v, 4) for k, v in result["dtmc_outcome_probabilities"].items()})
    print("PRISM on the DTMC:", prism_dtmc)


if __name__ == "__main__":
    main()
