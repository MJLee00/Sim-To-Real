#!/usr/bin/env python3

import argparse
from pathlib import Path

from overflowlight_exp.config_io import load_toml
from overflowlight_exp.planner import build_plan
from overflowlight_exp.simulator_s2r import run_simulator_sim2real
from overflowlight_exp.splits import materialize_splits
from overflowlight_exp.surrogate_sim import run_surrogate_sim2real


def cmd_prepare_splits(args):
    manifest_paths = materialize_splits(args.config_dir, args.output_dir)
    for path in manifest_paths:
        print("wrote split manifest: %s" % path)
    return 0


def cmd_plan(args):
    config_dir = Path(args.config_dir)
    global_paths = load_toml(config_dir / "global_paths.toml")
    split_root = args.split_dir or global_paths["paths"]["splits_root"]
    report_root = args.report_dir or global_paths["paths"]["reports_root"]
    plan_paths = build_plan(config_dir, split_root, report_root)
    for path in plan_paths:
        print("wrote experiment plan: %s" % path)
    return 0


def cmd_simulate_s2r(args):
    manifest = run_simulator_sim2real(
        config_dir=args.config_dir,
        output_root=args.output_root,
        days=args.days,
    )
    print("simulated %d intersections across %d cities" % (manifest["intersection_count"], manifest["city_count"]))
    print("source environment: %s" % manifest["source_environment"])
    print("target environment: %s" % manifest["target_environment"])
    print("records per environment: %d" % manifest["records_per_environment"])
    for name, path in sorted(manifest["outputs"].items()):
        print("wrote %s: %s" % (name, path))
    return 0


def build_parser():
    parser = argparse.ArgumentParser(description="OverFlowLight-S2R experiment pipeline")
    subparsers = parser.add_subparsers(dest="command")

    prepare = subparsers.add_parser("prepare-splits", help="Generate split manifests from the registry.")
    prepare.add_argument("--config-dir", default="experiments/configs")
    prepare.add_argument("--output-dir", default="/scratch/project_462001050/cache/overflowlight_s2r/splits")
    prepare.set_defaults(func=cmd_prepare_splits)

    plan = subparsers.add_parser("plan", help="Generate planning manifests for all configured experiments.")
    plan.add_argument("--config-dir", default="experiments/configs")
    plan.add_argument("--split-dir", default=None)
    plan.add_argument("--report-dir", default=None)
    plan.set_defaults(func=cmd_plan)

    simulate = subparsers.add_parser(
        "simulate-s2r",
        help="Run procedural CityFlow-to-SUMO simulator experiments for the 43-intersection registry.",
    )
    simulate.add_argument("--config-dir", default="experiments/configs")
    simulate.add_argument("--output-root", default=None)
    simulate.add_argument("--days", type=int, default=None)
    simulate.set_defaults(func=cmd_simulate_s2r)
    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        return 2
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
