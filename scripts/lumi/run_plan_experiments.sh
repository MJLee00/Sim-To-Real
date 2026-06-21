#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
cd "${PROJECT_ROOT}"

python3 experiments/run_experiment_pipeline.py plan
