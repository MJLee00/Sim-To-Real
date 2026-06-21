#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
CITYFLOW_SRC_DIR="${CITYFLOW_SRC_DIR:-/scratch/project_462001050/cache/src/CityFlow}"

cd "${PROJECT_ROOT}"

source .venv/bin/activate

python3 - <<'PY'
import pathlib
import site
import subprocess
import sys

import cityflow

site_paths = site.getsitepackages()
sumo_root = None
for base in site_paths:
    candidate = pathlib.Path(base) / "sumo"
    if candidate.is_dir():
        sumo_root = candidate
        break

if sumo_root is None:
    raise SystemExit("SUMO package root not found in site-packages")

for relative in ("bin/sumo", "bin/netconvert", "bin/duarouter", "tools/sumolib/__init__.py", "tools/traci/__init__.py"):
    path = sumo_root / relative
    if not path.exists():
        raise SystemExit(f"Missing SUMO artifact: {path}")

print(f"cityflow={cityflow.__file__}")
print(f"SUMO_HOME={sumo_root}")
print(subprocess.check_output([str(sumo_root / "bin" / "sumo"), "--version"], text=True).splitlines()[0])
print(subprocess.check_output([str(sumo_root / "bin" / "netconvert"), "--version"], text=True).splitlines()[0])
print(subprocess.check_output([str(sumo_root / "bin" / "duarouter"), "--version"], text=True).splitlines()[0])
PY

pushd "${CITYFLOW_SRC_DIR}" >/dev/null
export SUMO_HOME="$(python3 - <<'PY'
import pathlib
import site

for base in site.getsitepackages():
    candidate = pathlib.Path(base) / "sumo"
    if candidate.is_dir():
        print(candidate)
        break
else:
    raise SystemExit(1)
PY
)"
export PATH="${SUMO_HOME}/bin:${PATH}"
export PYTHONPATH="${SUMO_HOME}/tools${PYTHONPATH:+:${PYTHONPATH}}"
python3 -m unittest tests.python.test_api
python3 -m unittest tests.python.test_archive
popd >/dev/null
