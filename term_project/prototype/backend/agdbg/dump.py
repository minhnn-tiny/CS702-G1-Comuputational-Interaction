"""Print a recording's visible history as text (for coding ground-truth error lists): python -m agdbg.dump <recording> [chars]"""

from __future__ import annotations

import pickle
import sys

from .manager import RECORDINGS, visible
from .serialize import entry_json
from .tasks import TASKS

data = pickle.load((RECORDINGS / f"{sys.argv[1]}.pkl").open("rb"))
width = int(sys.argv[2]) if len(sys.argv) > 2 else 400
task = TASKS[data["task_id"]]
print(f"# {sys.argv[1]}  task={data['task_id']}  expected={task['expected']}\n{task['task']}\n")
for sid, sess in enumerate([*data["prior_sessions"], {"messages": [entry_json(e) for e in visible(data["history"])], "reset_from": data["reset_from"]}]):
    print(f"\n## session {sid} (forked from t={sess.get('reset_from')}) — {len(sess['messages'])} messages")
    for m in sess["messages"]:
        c = m["content"].replace("\n", " ⏎ ")
        print(f"[t={m['timestamp']:>3}] {m['sender']} -> {m['recipient']} ({m['type']}): {c[:width]}{'…' if len(c) > width else ''}")
for sid, j in data.get("suspects", {}).items():
    print(f"\n## judge, session {sid}: {j['summary']}")
    for s in j["suspects"]:
        print(f"  #{s['rank']} t={s['timestamp']} [{s['category']}] {s['reason']}\n     evidence={s['evidence']} suggestion={s['suggestion']}")
