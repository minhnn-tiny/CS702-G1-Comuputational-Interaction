#!/usr/bin/env bash
# Build the final report: Markdown -> ACM two-column PDF (pandoc + tectonic) and count the words.
set -euo pipefail
cd "$(dirname "$0")/.."
SRC=final_report.md
OUT=Final_Report_Group_Nguyen_Do.pdf
# Results section: the authored prose stays; the generated tables and figures from study/analyze.py are inserted at the
# <!-- TABLES --> marker when they exist (figures are copied to figures/results_*.png).
mkdir -p build
if [ -s ../prototype/study/results/results.md ]; then
  for f in ../prototype/study/results/*.png; do [ -e "$f" ] && cp "$f" "figures/results_$(basename "$f")"; done
  python3 - <<'PY'
import pathlib
src = pathlib.Path("final_report.md").read_text()
res = pathlib.Path("../prototype/study/results/results.md").read_text().split("\n", 2)[2]
res = res.replace("### ", "#### ")
src = src.replace("<!-- TABLES -->", res)
pathlib.Path("build/_report.md").write_text(src)
PY
else
  cp "$SRC" build/_report.md
fi
pandoc build/_report.md --from markdown+pipe_tables+implicit_figures --shift-heading-level-by=-1 --lua-filter build/tables.lua --template build/acm.latex --resource-path=.:figures -o build/_report.tex
tectonic -Z continue-on-errors -o build build/_report.tex > build/tectonic.log 2>&1 || { tail -20 build/tectonic.log; exit 1; }
mv build/_report.pdf "$OUT"
# word count: body text without the YAML header, figure captions, tables, code and the references section
python3 - <<'PY'
import re, pathlib
t = pathlib.Path("build/_report.md").read_text()
m = re.search(r"^abstract: \|\n((?:  .*\n)+)", t, flags=re.M)
abstract = m.group(1) if m else ""
t = abstract + re.sub(r"^---.*?---\s*", "", t, flags=re.S)
t = t.split("\n## References")[0]
t = re.sub(r"!\[.*?\]\(.*?\)", "", t, flags=re.S)
t = "\n".join(l for l in t.splitlines() if not l.strip().startswith("|") and not l.strip().startswith("```"))
t = re.sub(r"<!--.*?-->", "", t, flags=re.S)
words = re.findall(r"[A-Za-z0-9][A-Za-z0-9'’\-\.,/%]*", t)
print("words incl. abstract (excluding tables, figure captions, references):", len(words))
if len(words) > 3000:
    print("WARNING: over the 3,000-word limit")
PY
ls -la "$OUT"
