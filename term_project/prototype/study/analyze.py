"""Score the study data and write results/results.md (+ figures) for the final report.

    ../.venv/bin/python analyze.py              # reads data/*.csv, ../logs/*.jsonl, ground_truth/*.json -> results/
    ../.venv/bin/python analyze.py --selftest   # runs the same code on synthetic in-memory rows, writes nothing

Trials come from data/participants.csv (condition_order × task_order), so a trial in which nothing was found still
counts. Localisations come from two sources: flags in the logs (event "flag", matched to the ground truth by message
timestamp) and the rows of data/part1_localisation.csv (spoken localisations and facilitator corrections).
Only matplotlib is needed beyond the standard library.
"""

from __future__ import annotations

import csv
import io
import json
import math
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA, LOGS, GT, RES = HERE / "data", HERE.parent / "logs", HERE / "ground_truth", HERE / "results"
PAPER = {"helpful": 4.4, "easy_to_use": 4.0, "use_again": 4.6, "feat_send": 4.1, "feat_backtrack_edit": 4.9, "feat_overview": 4.1}
CONDITIONS = ["reduced", "full", "e1"]
TASK_RECORDING = {"A": "t13_fy_ratio_FAIL", "B": "t13_fy_ratio_FAIL_2", "C": "wt2_mongolia_rank_FAIL"}
TRIAL_SECONDS = 900


def read_csv(path: Path | None, text: str | None = None) -> list[dict[str, str]]:
    if text is None and (path is None or not path.exists()):
        return []
    f = io.StringIO(text) if text is not None else path.open()
    return [{k: (v or "").strip() for k, v in r.items()} for r in csv.DictReader(f) if any((v or "").strip() for v in r.values())]


def mean_ci(xs: list[float]) -> tuple[float, float, int]:
    """Mean, 95% CI half-width (t-distribution, 0 when n < 2) and n."""
    if not xs:
        return math.nan, 0.0, 0
    if len(xs) < 2:
        return xs[0], 0.0, 1
    t = {2: 12.71, 3: 4.30, 4: 3.18, 5: 2.78, 6: 2.57, 7: 2.45, 8: 2.36, 9: 2.31, 10: 2.26, 11: 2.23, 12: 2.20, 13: 2.18, 14: 2.16}.get(len(xs), 2.0)
    return st.mean(xs), t * st.stdev(xs) / math.sqrt(len(xs)), len(xs)


def fmt(m: float, ci: float, n: int) -> str:
    if n == 0:
        return "—"
    return f"{m:.2f}" if n == 1 else f"{m:.2f} ± {ci:.2f}"


def load_logs(log_dir: Path) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for f in sorted(log_dir.glob("P*.jsonl")) if log_dir.exists() else []:
        out[f.stem] = [json.loads(l) for l in f.read_text().splitlines() if l.strip()]
    return out


def trials(participants: list[dict[str, str]]) -> list[dict[str, str]]:
    """One record per (participant, condition, task) from the assignment columns 'condition_order' and 'task_order'
    (e.g. 'reduced,full,e1' and 'A,B,C'); only Part 1 participants have them."""
    out = []
    for p in participants:
        conds = [c.strip() for c in p.get("condition_order", "").split(",") if c.strip()]
        tasks = [t.strip() for t in p.get("task_order", "").split(",") if t.strip()]
        for pos, (c, t) in enumerate(zip(conds, tasks), 1):
            out.append({"id": p["id"], "condition": c, "task": t, "recording": TASK_RECORDING.get(t, t), "position": pos})
    return out


def part1(participants, loc, logs, gt) -> tuple[list[str], dict]:
    out, stats = [], {}
    tri = trials(participants)
    if not tri:
        return ["### Part 1 — error identification\n", "- no Part 1 participants yet (data/participants.csv)"], {}
    # localisations per trial: flags from the log (by message timestamp) + CSV rows (by ground-truth id)
    per_cond = defaultdict(lambda: defaultdict(list))
    cells = Counter()
    for tr in tri:
        g = gt.get(tr["recording"], {"errors": []})
        ids = {e["id"]: set(e["timestamps"]) for e in g["errors"]}
        prim = {e["id"] for e in g["errors"] if e.get("primary")}
        hits, first, false = set(), [], 0
        for ev in logs.get(tr["id"], []):
            if ev.get("event") == "flag" and ev.get("condition") == tr["condition"] and (ev.get("trial") or tr["task"]) == tr["task"]:
                matched = [k for k, ts in ids.items() if ev.get("timestamp") in ts]
                if matched:
                    hits.update(matched); first.append(float(ev.get("elapsed", TRIAL_SECONDS)))
                else:
                    false += 1
        for r in loc:
            if r["id"] == tr["id"] and r["condition"] == tr["condition"] and r.get("task", tr["task"]) == tr["task"]:
                if r.get("ground_truth_id") in ids and r.get("correct_1_0", "1") != "0":
                    hits.add(r["ground_truth_id"])
                    if r.get("clock_time_s"):
                        first.append(float(r["clock_time_s"]))
                elif r.get("ground_truth_id") not in ids:
                    false += 1
        d = per_cond[tr["condition"]]
        d["found"].append(len(hits) / max(1, len(ids)))
        d["primary"].append(1.0 if hits & prim else 0.0)
        d["any"].append(1.0 if hits else 0.0)
        if first:
            d["first"].append(min(first))
        d["false"].append(float(false))
        d["pos"].append(tr["position"])
        cells[(tr["condition"], tr["task"])] += 1
        rows = [r for r in loc if r["id"] == tr["id"] and r["condition"] == tr["condition"]]
        for k, col in (("conf", "confidence_1to5"), ("read", "read_amount_1to5")):
            vals = [float(r[col]) for r in rows if r.get(col)]
            if vals:
                d[k].append(vals[-1])
    out.append("### Part 1 — error identification by condition\n")
    out.append(f"{len(tri)} trials from {len({t['id'] for t in tri})} participants. Condition × task cells: " + ", ".join(f"{c}/{t}: {n}" for (c, t), n in sorted(cells.items())) + ".\n")
    out.append("| Condition | Trials | Share of coded errors found | Found a primary error | Found any error | Time to first correct localisation (s, trials with a hit) | False localisations per trial | Confidence (1–5) | Felt had to read (1–5) |")
    out.append("|---|---|---|---|---|---|---|---|---|")
    for c in CONDITIONS:
        d = per_cond[c]
        n = len(d["found"])
        out.append(f"| {c} | {n} | {fmt(*mean_ci(d['found']))} | {sum(d['primary']):.0f}/{n} | {sum(d['any']):.0f}/{n} | {fmt(*mean_ci(d['first']))} (n={len(d['first'])}) | {fmt(*mean_ci(d['false']))} | {fmt(*mean_ci(d['conf']))} | {fmt(*mean_ci(d['read']))} |")
        stats[c] = {k: list(v) for k, v in d.items()}
    pref = Counter(p.get("preference", "") for p in participants if p.get("preference"))
    if pref:
        out.append("\nPreference after the three tasks: " + ", ".join(f"{k} {v}" for k, v in pref.most_common()) + " (paper: 5 of 6 preferred full over reduced).")
    return out, stats


def part2(edits, ratings) -> tuple[list[str], dict]:
    out, stats = [], {}
    ids = sorted({r["id"] for r in ratings} | {r["id"] for r in edits})
    if not ids:
        return ["### Part 2 — steering\n", "- no Part 2 participants yet (data/ratings.csv)"], {}
    only_edits = [r for r in edits if r["kind_edit_send_reset_queue"] == "edit"]
    codes = Counter(r["code_add_simplify_modify"] for r in only_edits if r["code_add_simplify_modify"])
    per_p = {pid: sum(1 for r in only_edits if r["id"] == pid) for pid in ids}
    suspect_first = Counter()
    for pid in ids:
        mine = sorted((e for e in only_edits if e["id"] == pid), key=lambda e: float(e["clock_time_s"] or 0))
        if mine:
            suspect_first[mine[0]["was_suspect_1_0"] == "1"] += 1
    out.append("### Part 2 — steering\n")
    n = len(ratings)
    correct = sum(1 for r in ratings if r["final_outcome_correct_incorrect_unfinished"] == "correct")
    out.append(f"- Participants: {len(ids)}; reached the correct answer within 30 min: {correct}/{n} (paper: 2/8).")
    vals = list(per_p.values())
    out.append(f"- Message edits per participant (all {len(ids)} participants): median {st.median(vals):.0f}, range {min(vals)}–{max(vals)}; {sum(1 for v in vals if v == 0)} made no edit (paper: every participant edited at least once, 1–5 edits, 24 in total).")
    out.append(f"- Edit types (message edits only): add {codes.get('add', 0)}, simplify {codes.get('simplify', 0)}, modify {codes.get('modify', 0)} (paper: 14 / 5 / 5). Sends and queue edits: {sum(1 for r in edits if r['kind_edit_send_reset_queue'] in ('send', 'queue'))}; plain resets: {sum(1 for r in edits if r['kind_edit_send_reset_queue'] == 'reset')}.")
    if suspect_first:
        out.append(f"- First message edit was on a judge suspect: {suspect_first[True]}/{sum(suspect_first.values())} participants who edited.")
    tt = [float(r["time_to_first_edit_s"]) for r in ratings if r.get("time_to_first_edit_s")]
    if tt:
        out.append(f"- Time to first edit: {fmt(*mean_ci(tt))} s (n={len(tt)}).")
    out.append("\n### Part 2 — ratings (1–5, mean ± 95% CI, n)\n")
    out.append("| Item | Ours | n | Paper |")
    out.append("|---|---|---|---|")
    labels = {"helpful": "System helpful", "easy_to_use": "Easy to use", "use_again": "Would use again", "feat_send": "Feature: send new messages", "feat_backtrack_edit": "Feature: backtrack and edit", "feat_overview": "Feature: overview visualisation", "feat_context_panel": "Feature: error context panel (E1)"}
    for k, lab in labels.items():
        vals = [float(r[k]) for r in ratings if r.get(k)]
        m, ci, nn = mean_ci(vals)
        stats[k] = (m, ci, nn)
        out.append(f"| {lab} | {fmt(m, ci, nn)} | {nn} | {PAPER.get(k, '—')} |")
    stats["codes"] = codes
    return out, stats


def logs_summary(logs: dict[str, list[dict]]) -> list[str]:
    out = ["### Interaction log summary (logs/*.jsonl)\n"]
    if not logs:
        return out + ["- no participant logs yet"]
    out.append("| Participant | Condition | Trial | Events | Flags | Edits | Resets | Sends | Steps/Runs | Overview clicks | Suspects opened | Edit-from-context |")
    out.append("|---|---|---|---|---|---|---|---|---|---|---|---|")
    for pid, rows in logs.items():
        by = defaultdict(list)
        for r in rows:
            by[(r.get("condition"), r.get("trial", ""))].append(r)
        for (cond, trial), rs in by.items():
            c = Counter(r["event"] for r in rs)
            out.append(f"| {pid} | {cond} | {trial} | {len(rs)} | {c['flag']} | {c['edit']} | {c['reset']} | {c['send']} | {c['step'] + c['run']} | {c['overview_click']} | {c['suspect_open']} | {c['edit_from_context']} |")
    return out


def figures(p1: dict, p2: dict) -> list[str]:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return ["(matplotlib not installed: no figures)"]
    made = []
    labels = {"helpful": "Helpful", "easy_to_use": "Easy to use", "use_again": "Would use again", "feat_send": "Send message", "feat_backtrack_edit": "Backtrack & edit", "feat_overview": "Overview", "feat_context_panel": "Error context (E1)"}
    ks = [k for k in labels if k in p2 and p2[k][2] > 0]
    if ks:
        fig, ax = plt.subplots(figsize=(6, 3.2))
        y = list(range(len(ks)))
        ax.barh(y, [p2[k][0] for k in ks], xerr=[[min(p2[k][1], p2[k][0] - 1) for k in ks], [min(p2[k][1], 5 - p2[k][0]) for k in ks]], color="#4e79a7", capsize=3)
        for i, k in enumerate(ks):
            if k in PAPER:
                ax.plot([PAPER[k]], [i], marker="D", color="#e15759", ms=5)
        ax.set_yticks(y); ax.set_yticklabels([labels[k] for k in ks]); ax.set_xlim(1, 5); ax.invert_yaxis()
        ax.set_xlabel("Rating (1–5), mean ± 95% CI clipped to the scale; red diamond = paper's mean")
        fig.tight_layout(); fig.savefig(RES / "ratings.png", dpi=200); plt.close(fig)
        made.append(("ratings.png", "Part 2 ratings compared with the paper's means."))
    codes = p2.get("codes", Counter())
    if codes:
        fig, ax = plt.subplots(figsize=(4.5, 2.4))
        names = ["add", "simplify", "modify"]
        ax.barh(names, [codes.get(n, 0) for n in names], color=["#1b7837", "#c51b7d", "#d95f02"])
        ax.invert_yaxis(); ax.set_xlabel("Number of message edits"); fig.tight_layout(); fig.savefig(RES / "edit_types.png", dpi=200); plt.close(fig)
        made.append(("edit_types.png", "Edit types in Part 2 (paper: add 14, simplify 5, modify 5)."))
    if any(p1.get(c, {}).get("found") for c in CONDITIONS):
        fig, ax = plt.subplots(figsize=(5, 2.8))
        for i, c in enumerate(CONDITIONS):
            m, ci, n = mean_ci(p1.get(c, {}).get("found", []))
            if n:
                ax.bar(i, m, yerr=[[min(ci, m)], [min(ci, 1 - m)]], color=["#bab0ab", "#4e79a7", "#e11d48"][i], capsize=3)
        ax.set_xticks(range(3)); ax.set_xticklabels(CONDITIONS); ax.set_ylim(0, 1); ax.set_ylabel("Share of coded errors found")
        fig.tight_layout(); fig.savefig(RES / "part1_found.png", dpi=200); plt.close(fig)
        made.append(("part1_found.png", "Part 1: share of coded errors found per condition (mean ± 95% CI)."))
    return [f"![{cap}](figures/results_{name})" for name, cap in made]


def run(participants, loc, edits, ratings, gt, logs, write: bool) -> str:
    lines = ["# Study results (generated by study/analyze.py; tables are inserted into the final report by phase4/build/build.sh)", ""]
    a, p1 = part1(participants, loc, logs, gt)
    b, p2 = part2(edits, ratings)
    lines += a + [""] + b + [""] + logs_summary(logs)
    if write:
        RES.mkdir(exist_ok=True)
        lines += [""] + figures(p1, p2)
        (RES / "results.md").write_text("\n".join(lines) + "\n")
    return "\n".join(lines)


def selftest() -> None:
    gt = {"t13_fy_ratio_FAIL": {"errors": [{"id": "E1", "timestamps": [23], "primary": True}, {"id": "E2", "timestamps": [25]}, {"id": "E3", "timestamps": [32]}]},
          "t13_fy_ratio_FAIL_2": {"errors": [{"id": "E1", "timestamps": [36], "primary": True}, {"id": "E2", "timestamps": [47]}]}}
    participants = read_csv(None, "id,part,condition_order,task_order,preference\nP1,1,\"reduced,full,e1\",\"A,B,C\",e1\nP2,1,\"e1,reduced,full\",\"B,A,C\",full\nP7,2,,,\n")
    logs = {"P1": [{"event": "flag", "condition": "reduced", "trial": "A", "timestamp": 23, "elapsed": 400},
                   {"event": "flag", "condition": "reduced", "trial": "A", "timestamp": 99, "elapsed": 500},
                   {"event": "flag", "condition": "full", "trial": "B", "timestamp": 47, "elapsed": 200}],
            "P2": [{"event": "flag", "condition": "e1", "trial": "B", "timestamp": 36, "elapsed": 90}]}
    loc = read_csv(None, "id,condition,task,recording,clock_time_s,timestamp,participant_description,ground_truth_id,correct_1_0,flagged_1_0,confidence_1to5,read_amount_1to5\n"
                         "P1,e1,C,wt2_mongolia_rank_FAIL,,,nothing found,none,0,0,2,5\nP2,e1,B,t13_fy_ratio_FAIL_2,120,47,spoken,E2,1,0,5,2\n")
    edits = read_csv(None, "id,edit_no,clock_time_s,kind_edit_send_reset_queue,timestamp,sender_of_edited,was_suspect_1_0,code_add_simplify_modify,description,session_after,branch_outcome_correct_incorrect_unfinished\n"
                           "P7,1,300,edit,25,MagenticOneOrchestrator,1,add,x,1,incorrect\nP7,2,700,edit,9,MagenticOneOrchestrator,0,modify,x,2,correct\nP8,1,500,send,,,,,x,1,unfinished\n")
    ratings = read_csv(None, "id,helpful,easy_to_use,use_again,feat_send,feat_backtrack_edit,feat_overview,feat_context_panel,final_outcome_correct_incorrect_unfinished,n_edits,n_sessions,time_to_first_edit_s\n"
                             "P7,5,4,5,4,5,4,5,correct,2,2,300\nP8,4,4,4,3,5,4,4,unfinished,0,1,\n")
    text = run(participants, loc, edits, ratings, gt, logs, write=False)
    assert "6 trials from 2 participants" in text, text
    assert "| reduced | 2 | 0.17 ± 2.12 | 1/2 | 1/2 | 400.00 (n=1) | 0.50 ± 6.36 |" in text, text   # P1/A: E1 hit + 1 false; P2/A: nothing
    assert "| e1 | 2 | 0.50 ± 6.36 | 1/2 | 1/2 |" in text, text                                   # P2/B: E1 (flag) + E2 (spoken); P1/C: nothing
    assert "Preference after the three tasks: e1 1, full 1" in text, text
    assert "reached the correct answer within 30 min: 1/2" in text and "median 1, range 0–2; 1 made no edit" in text, text
    assert "add 1, simplify 0, modify 1" in text and "First message edit was on a judge suspect: 1/1" in text, text
    assert "| System helpful | 4.50 ± 6.36 | 2 | 4.4 |" in text, text
    print("selftest ok")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    else:
        gt = {p.stem: json.loads(p.read_text()) for p in GT.glob("*.json")}
        text = run(read_csv(DATA / "participants.csv"), read_csv(DATA / "part1_localisation.csv"), read_csv(DATA / "part2_edits.csv"), read_csv(DATA / "ratings.csv"), gt, load_logs(LOGS), write=True)
        print(text)
