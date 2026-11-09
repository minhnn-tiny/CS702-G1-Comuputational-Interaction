#!/usr/bin/env bash
# Assemble the Phase 4 submission: report PDF, 1-2 minute demo video, complete source code with README.
set -euo pipefail
cd "$(dirname "$0")"
./build/build.sh
rm -rf submission && mkdir -p submission
cp Final_Report_Group_Nguyen_Do.pdf submission/
cp final_demo_narrated.mp4 submission/Final_Demo_Group_Nguyen_Do.mp4
cp final_demo.vtt submission/Final_Demo_Group_Nguyen_Do.vtt
cp final_demo_transcript.md submission/Final_Demo_Group_Nguyen_Do_transcript.md
# source: the prototype without environments, build output, bulk recordings and study logs
rm -f submission/Source_Code_Group_Nguyen_Do.zip
(cd .. && zip -q -X -r phase4/submission/Source_Code_Group_Nguyen_Do.zip prototype phase4/final_report.md phase4/build phase4/figures phase4/README.md \
  -x 'prototype/.venv/*' 'prototype/frontend/node_modules/*' 'prototype/frontend/dist/*' 'prototype/workdir*' \
     'prototype/recordings/harvest/*' 'prototype/recordings/archive/*' 'prototype/recordings/harvest_logs/*' \
     'prototype/logs/*' 'prototype/study/results/*' '*/__pycache__/*' '*.pyc' '*.DS_Store' 'prototype/.env' \
     'phase4/build/_report.*' 'phase4/build/tectonic.log' 'phase4/build/figures')
rm -f phase4_submission.zip
(cd submission && zip -q -X -r ../phase4_submission.zip . -x '.DS_Store')
unzip -l phase4_submission.zip
du -h phase4_submission.zip
