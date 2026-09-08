"""Problem 2, Q1.b/Q1.d -- build the PRISM model and check the PCTL properties.

Runs ``prism healthline.pm healthline.props``, parses the results and
cross-checks every number with an independent value-iteration computation on
the Python definition of the MDP.  Writes outputs/verification.json.
"""

from __future__ import annotations

import json
import re

from healthline_mdp import HERE, OUT_DIR, TERMINAL, parse_results, reach_probability, run_prism, value_iteration


def python_reference() -> dict:
    """Independent computation of the same quantities (value iteration)."""
    vmax, pmax = value_iteration("max")
    vmin, pmin = value_iteration("min")
    success = set(TERMINAL) - {11}
    return {
        'Pmax=? [ F "resolved" ]': reach_probability({7}, "max")[0],
        'Pmin=? [ F "resolved" ]': reach_probability({7}, "min")[0],
        'Pmax=? [ F "abandoned" ]': reach_probability({11}, "max")[0],
        'Pmin=? [ F "abandoned" ]': reach_probability({11}, "min")[0],
        'Pmax=? [ F ("terminal"&!"abandoned") ]': reach_probability(success, "max")[0],
        'Pmin=? [ F ("terminal"&!"abandoned") ]': reach_probability(success, "min")[0],
        'R{"outcome"}max=? [ I=3 ]': vmax[0],
        'R{"outcome"}min=? [ I=3 ]': vmin[0],
        'R{"outcome"}max=? [ I=10 ]': vmax[0],
        "policy_max_reward": pmax,
        "policy_min_reward": pmin,
    }


def main() -> None:
    out = run_prism([str(HERE / "healthline.pm"), str(HERE / "healthline.props")])
    build = {}
    for key in ("States", "Transitions", "Choices"):
        m = re.search(rf"^{key}:\s+(\d+)", out, flags=re.M)
        if m:
            build[key.lower()] = int(m.group(1))
    prism_results = parse_results(out)
    ref = python_reference()
    norm = lambda s: re.sub(r"\s+", "", s)  # noqa: E731
    ref_norm = {norm(k): v for k, v in ref.items() if not k.startswith("policy")}
    rows = []
    for prop, val in prism_results:
        r = ref_norm.get(norm(prop))
        rows.append({"property": prop, "prism": val, "python_value_iteration": r,
                     "agree": (r is not None and abs(r - val) < 1e-6)})
    result = {"build": build, "properties": rows,
              "policy_max_reward": ref["policy_max_reward"], "policy_min_reward": ref["policy_min_reward"]}
    (OUT_DIR / "verification.json").write_text(json.dumps(result, indent=2))
    (OUT_DIR / "prism_verify_log.txt").write_text(out)
    print("PRISM build:", build)
    for r in rows:
        print(f"{r['property']:<45} PRISM = {r['prism']:.6f}   python = {r['python_value_iteration']:.6f}   agree = {r['agree']}")
    print("reward-maximising policy:", ref["policy_max_reward"])
    print("reward-minimising policy:", ref["policy_min_reward"])


if __name__ == "__main__":
    main()
