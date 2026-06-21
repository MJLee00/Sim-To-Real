#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
SIM_DAYS="${SIM_DAYS:-}"
cd "${PROJECT_ROOT}"

SIM_ARGS=()
if [[ -n "${SIM_DAYS}" ]]; then
    SIM_ARGS+=(--days "${SIM_DAYS}")
fi

python3 experiments/run_experiment_pipeline.py simulate-s2r "${SIM_ARGS[@]}"

RESULT_COPY_DIR="${RESULT_COPY_DIR:-experiments/results/cityflow_sumo_s2r}"
SOURCE_ROOT="/scratch/project_462001050/cache/overflowlight_s2r"

rm -rf "${RESULT_COPY_DIR}"
mkdir -p "${RESULT_COPY_DIR}"

cp -a "${SOURCE_ROOT}/data" "${RESULT_COPY_DIR}/"
cp -a "${SOURCE_ROOT}/reports" "${RESULT_COPY_DIR}/"
cp -a "${SOURCE_ROOT}/artifacts" "${RESULT_COPY_DIR}/"
cp -a "${SOURCE_ROOT}/splits" "${RESULT_COPY_DIR}/"

printf 'staged result package: %s\n' "${PROJECT_ROOT}/${RESULT_COPY_DIR}"
