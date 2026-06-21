#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
CITYFLOW_REPO_URL="${CITYFLOW_REPO_URL:-https://github.com/cityflow-project/CityFlow.git}"
CITYFLOW_REF="${CITYFLOW_REF:-master}"
CITYFLOW_SRC_DIR="${CITYFLOW_SRC_DIR:-/scratch/project_462001050/cache/src/CityFlow}"
SUMO_WHEEL_VERSION="${SUMO_WHEEL_VERSION:-1.27.0}"
PYBIND11_REF="${PYBIND11_REF:-v2.13.6}"

cd "${PROJECT_ROOT}"

source .venv/bin/activate

python3 -m pip install "eclipse-sumo==${SUMO_WHEEL_VERSION}" sympy mpmath

mkdir -p "$(dirname "${CITYFLOW_SRC_DIR}")"

if [[ ! -d "${CITYFLOW_SRC_DIR}/.git" ]]; then
    git clone --recursive "${CITYFLOW_REPO_URL}" "${CITYFLOW_SRC_DIR}"
fi

git -C "${CITYFLOW_SRC_DIR}" fetch --tags origin
git -C "${CITYFLOW_SRC_DIR}" checkout "${CITYFLOW_REF}"
git -C "${CITYFLOW_SRC_DIR}" submodule update --init --recursive
git -C "${CITYFLOW_SRC_DIR}/extern/pybind11" remote set-url origin https://github.com/pybind/pybind11.git
git -C "${CITYFLOW_SRC_DIR}/extern/pybind11" fetch --tags origin
git -C "${CITYFLOW_SRC_DIR}/extern/pybind11" checkout "${PYBIND11_REF}"

python3 -m pip install "${CITYFLOW_SRC_DIR}"

python3 - <<'PY'
import importlib.util
import pathlib
import site
import sys

site_paths = site.getsitepackages()
sumo_roots = []
for base in site_paths:
    candidate = pathlib.Path(base) / "sumo"
    if candidate.is_dir():
        sumo_roots.append(candidate)

if not sumo_roots:
    raise SystemExit("SUMO package root not found after eclipse-sumo install")

print(f"SUMO_HOME={sumo_roots[0]}")
print(f"SUMO tools={sumo_roots[0] / 'tools'}")
print(f"SUMO bin={sumo_roots[0] / 'bin'}")

spec = importlib.util.find_spec("cityflow")
if spec is None:
    raise SystemExit("cityflow module not importable after installation")
print(f"cityflow module={spec.origin}")
PY
