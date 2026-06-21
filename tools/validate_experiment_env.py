#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path
from typing import List, Tuple

try:
    import tomllib
except ImportError:  # pragma: no cover
    import tomli as tomllib


EXPECTED_ACCOUNT = "project_462001493"
EXPECTED_CACHE_PREFIX = "/scratch/project_462001050/cache/overflowlight_s2r"


def load_toml(path):
    with path.open("rb") as handle:
        return tomllib.load(handle)


def require(condition, message):
    if not condition:
        raise ValueError(message)


def validate_paths(config):
    paths = config.get("paths", {})
    require(paths, "global_paths.toml is missing [paths]")
    materialized = []
    for key, value in paths.items():
        require(
            isinstance(value, str) and value.startswith(EXPECTED_CACHE_PREFIX),
            f"path '{key}' must stay under {EXPECTED_CACHE_PREFIX}",
        )
        materialized.append(Path(value))
    return materialized


def validate_runtime(config):
    slurm = config.get("slurm", {})
    require(slurm.get("account") == EXPECTED_ACCOUNT, "runtime.toml has the wrong Slurm account")
    require(slurm.get("bootstrap_partition"), "runtime.toml is missing bootstrap_partition")
    require(slurm.get("cpu_partition"), "runtime.toml is missing cpu_partition")
    require(slurm.get("gpu_partition"), "runtime.toml is missing gpu_partition")


def validate_experiment_config(path, config):
    experiment = config.get("experiment", {})
    metrics = config.get("metrics", {})
    require(experiment.get("name"), f"{path.name} is missing experiment.name")
    require(experiment.get("output_subdir"), f"{path.name} is missing experiment.output_subdir")
    require(metrics.get("primary"), f"{path.name} is missing metrics.primary")
    return experiment["name"], experiment["output_subdir"]


def prepare_directories(base_dirs, output_subdirs):
    created = []
    for directory in base_dirs:
        directory.mkdir(parents=True, exist_ok=True)
        created.append(directory)

    named_roots = {path.name: path for path in base_dirs}
    for root_name in ("artifacts", "logs", "reports"):
        root = named_roots.get(root_name)
        if root is None:
            continue
        for output_subdir in output_subdirs:
            target = root / output_subdir
            target.mkdir(parents=True, exist_ok=True)
            created.append(target)
    return created


def main():
    parser = argparse.ArgumentParser(description="Validate OverFlowLight-S2R experiment settings.")
    parser.add_argument(
        "--config-dir",
        type=Path,
        default=Path("experiments/configs"),
        help="Directory containing TOML config files.",
    )
    parser.add_argument(
        "--prepare-dirs",
        action="store_true",
        help="Create the configured cache and output directories.",
    )
    args = parser.parse_args()

    config_dir = args.config_dir
    require(config_dir.is_dir(), f"config directory not found: {config_dir}")

    global_paths = load_toml(config_dir / "global_paths.toml")
    runtime = load_toml(config_dir / "runtime.toml")

    base_dirs = validate_paths(global_paths)
    validate_runtime(runtime)

    output_subdirs = []
    metadata_files = {
        "global_paths.toml",
        "runtime.toml",
        "dataset_registry.toml",
        "splits.toml",
        "method_registry.toml",
    }

    for path in sorted(config_dir.glob("*.toml")):
        if path.name in metadata_files:
            continue
        name, output_subdir = validate_experiment_config(path, load_toml(path))
        output_subdirs.append(output_subdir)
        print(f"validated config: {path.name} -> {name}")

    if args.prepare_dirs:
        created = prepare_directories(base_dirs, output_subdirs)
        for path in created:
            print(f"ensured directory: {path}")

    print(f"validated {len(output_subdirs)} experiment setting files")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ValueError as exc:
        print(f"validation error: {exc}", file=sys.stderr)
        raise SystemExit(1)
