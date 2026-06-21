#!/usr/bin/env bash
set -euo pipefail

export SBATCH_ACCOUNT="${SBATCH_ACCOUNT:-project_462001493}"
exec sbatch "$@"
