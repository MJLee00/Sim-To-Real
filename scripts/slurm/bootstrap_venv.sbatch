#!/bin/bash
#SBATCH --account=project_462001493
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=16G
#SBATCH --time=00:30:00
#SBATCH --job-name=ofl-bootstrap

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$SLURM_SUBMIT_DIR}"
cd "${PROJECT_ROOT}"

source scripts/lumi/common.sh

lumi_prepare_modules
lumi_configure_project_paths

printf -v CONTAINER_CMD 'cd %q && bash %q' "${PROJECT_ROOT}" "scripts/lumi/bootstrap_venv.sh"
srun "${LUMI_SINGULARITY_BIN:-/usr/bin/singularity}" run "$(lumi_default_sif)" bash -lc "${CONTAINER_CMD}"
