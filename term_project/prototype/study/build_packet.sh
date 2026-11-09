#!/usr/bin/env bash
# Printable facilitator packet: consent, task sheets, questionnaires, facilitator script -> study_packet.pdf
set -euo pipefail
cd "$(dirname "$0")"
pandoc consent_form.md task_sheets.md questionnaires.md facilitator_script.md \
  --from markdown --pdf-engine=tectonic -V geometry:margin=2cm -V fontsize=11pt -V mainfont="Helvetica" \
  --metadata title="Agent Team Debugger study — facilitator packet" -o study_packet.pdf
ls -la study_packet.pdf
