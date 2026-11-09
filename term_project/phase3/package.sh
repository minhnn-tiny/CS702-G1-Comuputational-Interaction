#!/usr/bin/env bash
# Assemble the Phase 3 submission: slides (PPTX with speaker notes), backup demo video, runbook.
set -euo pipefail
cd "$(dirname "$0")"
../prototype/.venv/bin/python slides/build_slides.py
rm -rf submission && mkdir submission
cp slides/Phase3_Slides_Group_Nguyen_Do.pptx submission/
cp phase3_demo_backup_narrated.mp4 submission/Phase3_Demo_Backup_Group_Nguyen_Do.mp4
cp phase3_demo_backup.vtt submission/Phase3_Demo_Backup_Group_Nguyen_Do.vtt
cp demo_runbook.md submission/Phase3_Live_Demo_Runbook.md
rm -f phase3_submission.zip
(cd submission && zip -q -X -r ../phase3_submission.zip . -x '.DS_Store')
unzip -l phase3_submission.zip
