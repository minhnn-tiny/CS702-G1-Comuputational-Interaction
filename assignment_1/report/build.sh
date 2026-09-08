#!/usr/bin/env bash
# Collect the figures produced by the problem scripts and compile the report.
set -euo pipefail
cd "$(dirname "$0")"
mkdir -p figures
cp ../problem1_bayesian/outputs/{fig_eda,fig_prior_predictive,fig_ppc,fig_posterior,plate_m1,plate_m2}.pdf figures/
cp ../problem2_healthline/outputs/{fig_mdp,fig_simulation}.pdf figures/
cp ../problem3_sequential/outputs/{fig_q1_regret,fig_q2_regret,fig_q2_learned,fig_q3}.pdf figures/
if command -v tectonic >/dev/null 2>&1; then
    tectonic -X compile report.tex
else
    pdflatex -interaction=nonstopmode report.tex && pdflatex -interaction=nonstopmode report.tex
fi
echo "built report.pdf"
