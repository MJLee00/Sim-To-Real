#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="${PROJECT_ROOT:-$(pwd)}"
CACHE_ROOT="${CACHE_ROOT:-/scratch/project_462001050/cache/overflowlight_s2r}"
cd "${PROJECT_ROOT}"

export PYTHONPATH="${PROJECT_ROOT}/experiments${PYTHONPATH:+:${PYTHONPATH}}"

python3 - <<'PY'
import csv
from pathlib import Path

from overflowlight_exp.surrogate_sim import (
    SETTING_TRANSFER_COMPACT_FIELDS,
    SETTING_TRANSFER_FIELDS,
    build_setting_transfer_results,
    compact_setting_transfer_table,
    write_csv,
)


STRING_FIELDS = {
    "environment",
    "intersection_id",
    "city",
    "city_label",
    "topology",
    "lane_profile",
    "risk_level",
    "time_window",
}


def load_rows(path):
    rows = []
    with Path(path).open("r", newline="") as handle:
        for row in csv.DictReader(handle):
            parsed = {}
            for key, value in row.items():
                if key in STRING_FIELDS or value is None or value == "":
                    parsed[key] = value
                    continue
                number = float(value)
                if key == "day_index":
                    parsed[key] = int(number)
                else:
                    parsed[key] = number
            rows.append(parsed)
    return rows


cache_root = Path("/scratch/project_462001050/cache/overflowlight_s2r")
data_root = cache_root / "data"
reports_root = cache_root / "reports"
artifacts_root = cache_root / "artifacts"

sumo_rows = load_rows(data_root / "sumo_target_dataset.csv")
cityflow_rows = load_rows(data_root / "cityflow_source_dataset.csv")

setting_detailed, setting_summary = build_setting_transfer_results(sumo_rows, cityflow_rows)
setting_compact = compact_setting_transfer_table(setting_summary)

write_csv(artifacts_root / "05_transfer_settings" / "setting_transfer_detailed.csv", setting_detailed)
write_csv(reports_root / "setting_transfer_summary.csv", setting_summary, SETTING_TRANSFER_FIELDS)
write_csv(reports_root / "setting_transfer_compact.csv", setting_compact, SETTING_TRANSFER_COMPACT_FIELDS)

print("wrote setting summary: %s" % (reports_root / "setting_transfer_summary.csv"))
print("wrote setting compact: %s" % (reports_root / "setting_transfer_compact.csv"))
print("wrote setting detailed: %s" % (artifacts_root / "05_transfer_settings" / "setting_transfer_detailed.csv"))
PY
