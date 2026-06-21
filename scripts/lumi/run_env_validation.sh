#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
cd "${PROJECT_ROOT}"

python3 --version
python3 tools/validate_experiment_env.py --config-dir experiments/configs --prepare-dirs
