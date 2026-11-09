# Phase 4 deliverables

- `final_report.md` — report source (Markdown with a YAML header). `build/build.sh` renders it to
  `Final_Report_Group_Nguyen_Do.pdf` with pandoc, the ACM `acmart` class (via tectonic, which downloads it on first
  use) and `build/tables.lua`; the script prints the word count. When `../prototype/study/results/results.md`
  exists (written by `../prototype/study/analyze.py` after the study), its tables and figures are inserted at the
  `<!-- TABLES -->` marker of the Results section.
- `final_demo.mp4` / `final_demo_narrated.mp4` / `.vtt` / `_transcript.md` — the 1–2 minute demo, recorded with
  `../prototype/frontend/scripts/demo_e1.mjs scripts/final.config.json` (see the prototype README).
- `package.sh` — rebuilds the PDF and assembles `submission/` and `phase4_submission.zip` (report, video, source zip).
- `figures/` — architecture diagram (`architecture.dot` → `.png` with graphviz) and UI screenshots.
