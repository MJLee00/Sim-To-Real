#!/usr/bin/env python3

import json
from datetime import datetime
from pathlib import Path

from .config_io import load_toml


def _load_split_manifest(split_root, split_name):
    path = Path(split_root) / (split_name + ".json")
    if not path.exists():
        raise ValueError("split manifest not found: %s" % path)
    with path.open("r") as handle:
        return json.load(handle)


def _expand_methods(experiment_name, experiment_cfg):
    if experiment_name == "simulator_fidelity":
        methods = experiment_cfg.get("environments", {}).get("defaults", []) + experiment_cfg.get("environments", {}).get("candidates", [])
        return [{"method": method, "role": "environment"} for method in methods]
    if experiment_name == "sim2real_transfer":
        methods = experiment_cfg.get("methods", {}).get("baseline", []) + experiment_cfg.get("methods", {}).get("proposed", [])
        return [{"method": method, "role": "controller"} for method in methods]
    if experiment_name == "cross_generalization":
        scenarios = experiment_cfg.get("settings", {}).get("scenarios", [])
        budgets = experiment_cfg.get("few_shot", {}).get("budgets", [])
        expanded = []
        for scenario in scenarios:
            for budget in budgets:
                expanded.append({"scenario": scenario, "budget": budget})
        return expanded
    if experiment_name == "domain_gap_robustness":
        perturbations = experiment_cfg.get("perturbations", {})
        expanded = []
        for name, values in sorted(perturbations.items()):
            for value in values:
                expanded.append({"perturbation": name, "setting": value})
        return expanded
    raise ValueError("unknown experiment name: %s" % experiment_name)


def build_plan(config_dir, split_root, report_root):
    config_dir = Path(config_dir)
    report_root = Path(report_root)
    report_root.mkdir(parents=True, exist_ok=True)

    global_paths = load_toml(config_dir / "global_paths.toml")
    runtime = load_toml(config_dir / "runtime.toml")
    method_registry = load_toml(config_dir / "method_registry.toml")

    plans = []
    experiment_files = sorted(
        path for path in config_dir.glob("*.toml")
        if path.name not in {
            "global_paths.toml",
            "runtime.toml",
            "dataset_registry.toml",
            "splits.toml",
            "method_registry.toml",
        }
    )

    for path in experiment_files:
        cfg = load_toml(path)
        meta = cfg["experiment"]
        name = meta["name"]

        split_info = cfg.get("splits", {})
        resolved_splits = {}
        for key, split_name in sorted(split_info.items()):
            manifest = _load_split_manifest(split_root, split_name)
            resolved_splits[key] = {
                "split_name": split_name,
                "intersection_count": manifest["intersection_count"],
            }

        plan = {
            "experiment_name": name,
            "goal": meta.get("goal"),
            "output_subdir": meta.get("output_subdir"),
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "runtime": runtime.get("runtime", {}),
            "slurm": runtime.get("slurm", {}),
            "paths": global_paths.get("paths", {}),
            "splits": resolved_splits,
            "work_items": _expand_methods(name, cfg),
        }

        if name == "sim2real_transfer":
            methods = plan["work_items"]
            for item in methods:
                method_name = item["method"]
                item["registry"] = method_registry.get("methods", {}).get(method_name, {})

        target = report_root / (name + "_plan.json")
        with target.open("w") as handle:
            json.dump(plan, handle, indent=2, sort_keys=True)
            handle.write("\n")
        plans.append(target)

    return plans
