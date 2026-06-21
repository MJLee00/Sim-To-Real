#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
cd "${PROJECT_ROOT}"

if [[ -f .venv.sqsh ]]; then
    rm -f .venv.sqsh
fi

if [[ -d .venv ]]; then
    rm -rf .venv
fi

python3 -m venv .venv --system-site-packages
source .venv/bin/activate

python3 -m pip install --upgrade pip

requirements_file=""
if [[ -f requirements-lumi.txt ]]; then
    requirements_file="requirements-lumi.txt"
elif [[ -f requirements.txt ]]; then
    requirements_file="requirements.txt"
fi

if [[ -n "${requirements_file}" ]]; then
    python3 -m pip install -r "${requirements_file}"
fi

if [[ -f pyproject.toml ]]; then
    python3 -m pip install -e . --no-deps
fi

if command -v mksquashfs >/dev/null 2>&1; then
    mksquashfs .venv .venv.sqsh -noappend -comp zstd -processors "${SLURM_CPUS_PER_TASK:-4}"
fi
