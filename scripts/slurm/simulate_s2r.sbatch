#!/bin/bash
#SBATCH --account=project_462001493
#SBATCH --partition=small
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --mem=24G
#SBATCH --time=02:00:00
#SBATCH --job-name=ofl-s2r-sim

set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$SLURM_SUBMIT_DIR}"
PAYLOAD_SCRIPT="${PAYLOAD_SCRIPT:-scripts/lumi/run_sim2real_surrogate.sh}"
cd "${PROJECT_ROOT}"

source scripts/lumi/common.sh

lumi_prepare_modules
lumi_configure_project_paths
lumi_prepare_venv_mount
lumi_prepare_sumo_env

printf -v CONTAINER_CMD 'cd %q && %s && bash %q' "${PROJECT_ROOT}" "${LUMI_VENV_ACTIVATE}" "${PAYLOAD_SCRIPT}"
lumi_run_container "${CONTAINER_CMD}"
