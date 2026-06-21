#!/usr/bin/env python3

import json
from pathlib import Path

from .config_io import load_toml


def _registry_index(registry):
    cities = registry.get("cities", {})
    by_id = {}
    for city_key, city_info in cities.items():
        for item in city_info.get("intersections", []):
            record = dict(item)
            record["city"] = city_key
            record["city_label"] = city_info.get("label", city_key)
            by_id[record["id"]] = record
    return by_id


def materialize_splits(config_dir, output_dir):
    config_dir = Path(config_dir)
    output_dir = Path(output_dir)
    registry = load_toml(config_dir / "dataset_registry.toml")
    split_cfg = load_toml(config_dir / "splits.toml")

    by_id = _registry_index(registry)
    split_defs = split_cfg.get("splits", {})

    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_paths = []
    for split_name, split_info in sorted(split_defs.items()):
        if split_name in ("version", "description"):
            continue
        ids = split_info.get("intersections", [])
        records = []
        missing = []
        for intersection_id in ids:
            if intersection_id not in by_id:
                missing.append(intersection_id)
                continue
            records.append(by_id[intersection_id])
        if missing:
            raise ValueError("missing intersections in registry for split %s: %s" % (split_name, ",".join(missing)))

        payload = {
            "split_name": split_name,
            "intersection_count": len(records),
            "notes": split_info.get("notes", []),
            "intersections": records,
        }
        target = output_dir / (split_name + ".json")
        with target.open("w") as handle:
            json.dump(payload, handle, indent=2, sort_keys=True)
            handle.write("\n")
        manifest_paths.append(target)

    return manifest_paths
