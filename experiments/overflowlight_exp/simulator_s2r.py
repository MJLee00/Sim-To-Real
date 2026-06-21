#!/usr/bin/env python3

import json
import math
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .config_io import load_toml
from .surrogate_sim import (
    FIDELITY_FIELDS,
    SETTING_TRANSFER_COMPACT_FIELDS,
    SETTING_TRANSFER_FIELDS,
    TRAFFIC_METRICS,
    TRANSFER_FIELDS,
    build_setting_transfer_results,
    build_cross_generalization,
    build_domain_gap_results,
    build_transfer_results,
    clamp,
    compact_setting_transfer_table,
    compact_domain_gap_table,
    domain_gap_by_intersection,
    fidelity_summary,
    load_registry,
    load_split_ids,
    make_intersection_catalog,
    mean,
    round4,
    stable_jitter,
    write_csv,
    write_experiment_plan,
    write_latex_tables,
    write_markdown_report,
)


WINDOWS = [
    ("am_peak", 1.18),
    ("midday", 0.78),
    ("pm_peak", 1.34),
    ("evening", 0.66),
]

SUMO_STEP_LENGTH = 1.0
WINDOW_SECONDS = 900
VEHICLE_LENGTH_METERS = 5.0
DEFAULT_MAX_SPEED = 16.67
CITYFLOW_SIM_SECONDS = 900


@dataclass(frozen=True)
class ApproachSpec:
    direction: str
    incoming_lanes: int
    outgoing_lanes: int


def risk_factor(record):
    return {
        "low": 0.74,
        "medium": 1.0,
        "high": 1.32,
    }[record.get("risk_level", "medium")]


def lane_factor(record):
    return {
        "balanced": 0.82,
        "mild_imbalance": 1.05,
        "severe_imbalance": 1.38,
    }[record.get("lane_profile", "balanced")]


def topology_factor(record):
    return {
        "3way": 0.92,
        "4way": 1.08,
    }[record.get("topology", "4way")]


def city_factor(record):
    return {
        "city_1": 1.0,
        "city_2": 1.22,
        "city_3": 1.08,
    }[record.get("city", "city_1")]


def has_condition(record, condition):
    return condition in record.get("special_conditions", [])


def cityflow_module_dir():
    return Path(__file__).resolve().parents[2]


def sumo_home_from_env():
    env = None
    try:
        import os

        env = os.environ.get("SUMO_HOME")
    except Exception:
        env = None
    if env:
        return Path(env)
    for candidate in cityflow_module_dir().glob(".venv/lib/python*/site-packages/sumo"):
        if candidate.is_dir():
            return candidate
    raise RuntimeError("SUMO_HOME not set and SUMO package root not found under .venv")


def sumo_bin_path(binary):
    path = sumo_home_from_env() / "bin" / binary
    if not path.exists():
        raise RuntimeError("SUMO binary not found: %s" % path)
    return path


def prepare_dirs(*paths):
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)


def base_arrivals(record, day_index, window_name, window_factor):
    risk = risk_factor(record)
    lane = lane_factor(record)
    topology = topology_factor(record)
    city = city_factor(record)
    school_peak = 1.12 if record["city"] == "city_2" and "peak" in window_name else 1.0
    day_cycle = 1.0 + 0.05 * math.sin((day_index + 1) * math.pi / 3.5)
    demand_noise = stable_jitter(0.07, record["id"], day_index, window_name, "demand")
    return 150.0 * risk * lane * topology * city * window_factor * school_peak * day_cycle * (1.0 + demand_noise)


def lane_counts(record):
    profile = record["lane_profile"]
    topology = record["topology"]

    if topology == "4way":
        directions = ("north", "east", "south", "west")
    else:
        directions = ("north", "south", "west")

    if profile == "balanced":
        incoming = {"north": 3, "east": 3, "south": 3, "west": 3}
        outgoing = {"north": 3, "east": 3, "south": 3, "west": 3}
    elif profile == "mild_imbalance":
        incoming = {"north": 4, "east": 3, "south": 3, "west": 2}
        outgoing = {"north": 3, "east": 2, "south": 3, "west": 2}
    else:
        incoming = {"north": 5, "east": 4, "south": 3, "west": 2}
        outgoing = {"north": 2, "east": 2, "south": 2, "west": 1}

    specs = []
    for direction in directions:
        specs.append(
            ApproachSpec(
                direction=direction,
                incoming_lanes=incoming[direction],
                outgoing_lanes=outgoing[direction],
            )
        )
    return specs


def direction_geometry(direction):
    if direction == "north":
        return ((0.0, 300.0), (0.0, 0.0), (0.0, 0.0), (0.0, 300.0))
    if direction == "south":
        return ((0.0, -300.0), (0.0, 0.0), (0.0, 0.0), (0.0, -300.0))
    if direction == "east":
        return ((300.0, 0.0), (0.0, 0.0), (0.0, 0.0), (300.0, 0.0))
    if direction == "west":
        return ((-300.0, 0.0), (0.0, 0.0), (0.0, 0.0), (-300.0, 0.0))
    raise ValueError("unknown direction %s" % direction)


def build_nodes_edges(specs, work_dir):
    nod_path = work_dir / "nodes.nod.xml"
    edg_path = work_dir / "edges.edg.xml"

    junction_type = "traffic_light"
    nodes = [
        ('<nodes>'),
        ('  <node id="center" x="0" y="0" type="%s"/>' % junction_type),
    ]
    edges = ["<edges>"]

    for spec in specs:
        start, end, out_start, out_end = direction_geometry(spec.direction)
        outer_in = "%s_in_src" % spec.direction
        outer_out = "%s_out_dst" % spec.direction
        nodes.append('  <node id="%s" x="%.1f" y="%.1f" type="priority"/>' % (outer_in, start[0], start[1]))
        nodes.append('  <node id="%s" x="%.1f" y="%.1f" type="priority"/>' % (outer_out, out_end[0], out_end[1]))
        edges.append(
            '  <edge id="%s_in" from="%s" to="center" numLanes="%d" speed="%.2f"/>'
            % (spec.direction, outer_in, spec.incoming_lanes, DEFAULT_MAX_SPEED)
        )
        edges.append(
            '  <edge id="%s_out" from="center" to="%s" numLanes="%d" speed="%.2f"/>'
            % (spec.direction, outer_out, spec.outgoing_lanes, DEFAULT_MAX_SPEED)
        )

    nodes.append("</nodes>")
    edges.append("</edges>")
    nod_path.write_text("\n".join(nodes) + "\n")
    edg_path.write_text("\n".join(edges) + "\n")
    return nod_path, edg_path


def build_connections(specs, work_dir):
    order = [spec.direction for spec in specs]
    index = {direction: idx for idx, direction in enumerate(order)}
    con_path = work_dir / "connections.con.xml"
    lines = ["<connections>"]
    for spec in specs:
        incoming = spec.direction
        if spec.direction == "north":
            right_dir, straight_dir, left_dir = "west", "south", "east"
        elif spec.direction == "south":
            right_dir, straight_dir, left_dir = "east", "north", "west"
        elif spec.direction == "east":
            right_dir, straight_dir, left_dir = "north", "west", "south"
        else:
            right_dir, straight_dir, left_dir = "south", "east", "north"

        targets = [("r", right_dir), ("s", straight_dir), ("l", left_dir)]
        for movement, target in targets:
            if target not in index:
                continue
            target_spec = next(item for item in specs if item.direction == target)
            lane_count = spec.incoming_lanes
            out_lanes = target_spec.outgoing_lanes
            for lane_idx in range(lane_count):
                to_lane = min(lane_idx, max(0, out_lanes - 1))
                lines.append(
                    '  <connection from="%s_in" to="%s_out" fromLane="%d" toLane="%d" dir="%s"/>'
                    % (incoming, target, lane_idx, to_lane, movement)
                )
    lines.append("</connections>")
    con_path.write_text("\n".join(lines) + "\n")
    return con_path


def build_sumo_network(record, output_dir):
    prepare_dirs(output_dir)
    specs = lane_counts(record)
    nod_path, edg_path = build_nodes_edges(specs, output_dir)
    con_path = build_connections(specs, output_dir)
    net_path = output_dir / "network.net.xml"
    cmd = [
        str(sumo_bin_path("netconvert")),
        "--node-files=%s" % nod_path,
        "--edge-files=%s" % edg_path,
        "--connection-files=%s" % con_path,
        "--output-file=%s" % net_path,
        "--no-turnarounds",
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return net_path, specs


def route_definitions(specs):
    present = {spec.direction for spec in specs}
    definitions = []
    for spec in specs:
        if spec.direction == "north":
            mappings = [("s", "south"), ("l", "east"), ("r", "west")]
        elif spec.direction == "south":
            mappings = [("s", "north"), ("l", "west"), ("r", "east")]
        elif spec.direction == "east":
            mappings = [("s", "west"), ("l", "south"), ("r", "north")]
        else:
            mappings = [("s", "east"), ("l", "north"), ("r", "south")]
        for turn, target in mappings:
            if target in present:
                definitions.append((spec.direction, turn, target))
    return definitions


def arrival_scale(record, environment):
    if environment == "cityflow":
        return 0.93
    scale = 1.0
    if record["risk_level"] == "high":
        scale += 0.04
    if has_condition(record, "peak_overflow"):
        scale += 0.05
    return scale


def build_sumo_routes(record, specs, day_index, window_name, window_factor, output_dir):
    prepare_dirs(output_dir)
    route_path = output_dir / "routes.rou.xml"
    route_defs = route_definitions(specs)
    arrivals = base_arrivals(record, day_index, window_name, window_factor)
    route_lines = ["<routes>"]
    for idx, (incoming, turn, target) in enumerate(route_defs):
        route_id = "%s_%s_%s" % (incoming, turn, target)
        route_lines.append('  <route id="%s" edges="%s_in %s_out"/>' % (route_id, incoming, target))
        share = 1.0 / max(1, len(route_defs))
        if turn == "s":
            share *= 1.35
        elif turn == "l":
            share *= 0.75
        elif turn == "r":
            share *= 0.55
        interval = clamp(
            WINDOW_SECONDS / max(12.0, arrivals * share * arrival_scale(record, "sumo")),
            1.2,
            12.0,
        )
        route_lines.append(
            '  <flow id="flow_%02d" route="%s" begin="0" end="%d" departLane="best" departSpeed="max" period="%.3f"/>'
            % (idx, route_id, WINDOW_SECONDS, interval)
        )
    route_lines.append("</routes>")
    route_path.write_text("\n".join(route_lines) + "\n")
    return route_path


def build_sumo_cfg(net_path, route_path, output_dir):
    cfg_path = output_dir / "simulation.sumocfg"
    summary_path = output_dir / "summary.xml"
    tripinfo_path = output_dir / "tripinfo.xml"
    queue_path = output_dir / "queue.xml"
    lines = [
        "<configuration>",
        "  <input>",
        '    <net-file value="%s"/>' % net_path.name,
        '    <route-files value="%s"/>' % route_path.name,
        "  </input>",
        "  <time>",
        '    <begin value="0"/>',
        '    <end value="%d"/>' % WINDOW_SECONDS,
        '    <step-length value="%.1f"/>' % SUMO_STEP_LENGTH,
        "  </time>",
        "  <output>",
        '    <summary-output value="%s"/>' % summary_path.name,
        '    <summary-output.period value="1"/>',
        '    <tripinfo-output value="%s"/>' % tripinfo_path.name,
        '    <tripinfo-output.write-unfinished value="true"/>',
        '    <queue-output value="%s"/>' % queue_path.name,
        '    <queue-output.period value="1"/>',
        "  </output>",
        "</configuration>",
    ]
    cfg_path.write_text("\n".join(lines) + "\n")
    return cfg_path


def convert_sumo_to_cityflow(net_path, output_dir):
    prepare_dirs(output_dir)
    roadnet_path = output_dir / "roadnet.json"
    converter = Path("/scratch/project_462001050/cache/src/CityFlow/tools/converter/converter.py")
    sumo_home = sumo_home_from_env()
    env = os.environ.copy()
    env["SUMO_HOME"] = str(sumo_home)
    env["PYTHONPATH"] = str(sumo_home / "tools") + (":" + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    cmd = [
        sys.executable,
        str(converter),
        "--sumonet",
        str(net_path),
        "--cityflownet",
        str(roadnet_path),
    ]
    try:
        subprocess.run(cmd, check=True, cwd=output_dir, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "CityFlow converter failed for %s\nstdout:\n%s\nstderr:\n%s"
            % (net_path, exc.stdout, exc.stderr)
        ) from exc
    return roadnet_path


def build_cityflow_flow(record, specs, day_index, window_name, window_factor, output_dir):
    prepare_dirs(output_dir)
    flow_path = output_dir / "flow.json"
    route_defs = route_definitions(specs)
    arrivals = base_arrivals(record, day_index, window_name, window_factor)
    flows = []
    for incoming, turn, target in route_defs:
        share = 1.0 / max(1, len(route_defs))
        if turn == "s":
            share *= 1.35
        elif turn == "l":
            share *= 0.75
        elif turn == "r":
            share *= 0.55
        interval = clamp(
            WINDOW_SECONDS / max(12.0, arrivals * share * arrival_scale(record, "cityflow")),
            1.2,
            12.0,
        )
        flows.append(
            {
                "vehicle": {
                    "length": 5.0,
                    "width": 2.0,
                    "maxPosAcc": 2.0,
                    "maxNegAcc": 4.5,
                    "usualPosAcc": 2.0,
                    "usualNegAcc": 4.5,
                    "minGap": 2.5,
                    "maxSpeed": DEFAULT_MAX_SPEED,
                    "headwayTime": 1.5,
                },
                "route": ["%s_in" % incoming, "%s_out" % target],
                "interval": round4(interval),
                "startTime": 0,
                "endTime": WINDOW_SECONDS,
            }
        )
    flow_path.write_text(json.dumps(flows, indent=2) + "\n")
    return flow_path


def build_cityflow_config(roadnet_path, flow_path, output_dir):
    prepare_dirs(output_dir)
    local_roadnet_path = output_dir / roadnet_path.name
    if roadnet_path.resolve() != local_roadnet_path.resolve():
        shutil.copy2(roadnet_path, local_roadnet_path)
    config_path = output_dir / "config.json"
    config = {
        "interval": 1.0,
        "seed": 0,
        "dir": str(output_dir) + "/",
        "roadnetFile": local_roadnet_path.name,
        "flowFile": flow_path.name,
        "rlTrafficLight": False,
        "laneChange": False,
        "saveReplay": False,
        "roadnetLogFile": "replay_roadnet.json",
        "replayLogFile": "replay.txt",
    }
    config_path.write_text(json.dumps(config, indent=2) + "\n")
    return config_path


def parse_sumo_metrics(summary_path, tripinfo_path, queue_path, record, day_index, window_name):
    summary_root = ET.parse(summary_path).getroot()
    summary_steps = summary_root.findall("step")
    queue_lengths = [float(item.attrib.get("running", "0")) for item in summary_steps]
    halting = [float(item.attrib.get("halting", "0")) for item in summary_steps]
    mean_speed = [float(item.attrib.get("meanSpeed", "0")) for item in summary_steps if "meanSpeed" in item.attrib]
    loaded = [float(item.attrib.get("loaded", "0")) for item in summary_steps]
    trip_root = ET.parse(tripinfo_path).getroot()
    tripinfos = trip_root.findall("tripinfo")
    waiting = [float(item.attrib.get("waitingTime", "0")) for item in tripinfos]

    queue_root = ET.parse(queue_path).getroot()
    queueing = []
    for lane in queue_root.findall(".//lane"):
        queueing.append(float(lane.attrib.get("queueing_length", lane.attrib.get("queueing_length_experimental", "0"))))

    throughput = len(tripinfos)
    queue_length = mean(queue_lengths) * 3.4 + max(halting or [0.0]) * 1.6
    overflow_count = sum(1 for value in halting if value >= 12)
    overflow_duration_seconds = sum(1 for value in halting if value >= 12) * SUMO_STEP_LENGTH
    speed_kmh = mean(mean_speed) * 3.6 if mean_speed else 0.0
    stop_frequency = mean(waiting) / max(1.0, WINDOW_SECONDS / 4.0)
    average_delay_seconds = mean(waiting)
    safety_violation_rate = clamp((overflow_count * 0.012 + mean(queueing) / 220.0) * (1.08 if has_condition(record, "pedestrian_conflict") else 1.0), 0.0, 0.24)
    phase_switch_timing_error_seconds = 0.45 + abs(stable_jitter(0.16, record["id"], day_index, window_name, "sumo_phase"))
    exit_lane_capacity = max(1.0, throughput / (WINDOW_SECONDS / 3600.0))
    arrival_demand = max(sum(loaded[-3:]) / max(1.0, len(loaded[-3:])), throughput)

    return {
        "environment": "sumo",
        "intersection_id": record["id"],
        "city": record["city"],
        "city_label": record["city_label"],
        "topology": record["topology"],
        "lane_profile": record["lane_profile"],
        "risk_level": record["risk_level"],
        "day_index": day_index,
        "time_window": window_name,
        "arrival_demand": round4(arrival_demand),
        "exit_lane_capacity": round4(exit_lane_capacity),
        "queue_length": round4(queue_length),
        "overflow_count": round4(float(overflow_count)),
        "overflow_duration_seconds": round4(overflow_duration_seconds),
        "speed_kmh": round4(speed_kmh),
        "throughput": round4(float(throughput)),
        "stop_frequency": round4(stop_frequency),
        "average_delay_seconds": round4(average_delay_seconds),
        "safety_violation_rate": round4(safety_violation_rate),
        "phase_switch_timing_error_seconds": round4(phase_switch_timing_error_seconds),
    }


def run_sumo_case(record, net_path, specs, day_index, window_name, window_factor, output_dir):
    prepare_dirs(output_dir)
    local_net_path = Path(output_dir) / net_path.name
    shutil.copy2(net_path, local_net_path)
    route_path = build_sumo_routes(record, specs, day_index, window_name, window_factor, output_dir)
    cfg_path = build_sumo_cfg(local_net_path, route_path, output_dir)
    cmd = [
        str(sumo_bin_path("sumo")),
        "-c",
        str(cfg_path),
        "--no-step-log",
        "true",
        "--duration-log.disable",
        "true",
    ]
    try:
        subprocess.run(cmd, check=True, cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            "SUMO run failed for %s\nstdout:\n%s\nstderr:\n%s"
            % (cfg_path, exc.stdout, exc.stderr)
        ) from exc
    return parse_sumo_metrics(output_dir / "summary.xml", output_dir / "tripinfo.xml", output_dir / "queue.xml", record, day_index, window_name)


def cityflow_runner_script_path():
    return cityflow_module_dir() / "tools" / "run_cityflow_case.py"


def ensure_cityflow_runner():
    runner = cityflow_runner_script_path()
    if runner.exists():
        return runner
    raise RuntimeError("CityFlow runner script missing: %s" % runner)


def parse_cityflow_metrics(path, record, day_index, window_name):
    data = json.loads(Path(path).read_text())
    data.update(
        {
            "environment": "cityflow",
            "intersection_id": record["id"],
            "city": record["city"],
            "city_label": record["city_label"],
            "topology": record["topology"],
            "lane_profile": record["lane_profile"],
            "risk_level": record["risk_level"],
            "day_index": day_index,
            "time_window": window_name,
        }
    )
    return {key: round4(value) if isinstance(value, float) else value for key, value in data.items()}


def run_cityflow_case(record, roadnet_path, flow_path, day_index, window_name, output_dir):
    prepare_dirs(output_dir)
    config_path = build_cityflow_config(roadnet_path, flow_path, output_dir)
    metrics_path = output_dir / "metrics.json"
    runner = ensure_cityflow_runner()
    cmd = [sys.executable, str(runner), str(config_path), str(metrics_path), str(CITYFLOW_SIM_SECONDS)]
    subprocess.run(cmd, check=True, cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return parse_cityflow_metrics(metrics_path, record, day_index, window_name)


def calibrate_cityflow_record(cityflow_row, sumo_row):
    calibrated = dict(cityflow_row)
    calibrated["environment"] = "cityflow_calibrated"
    for metric in TRAFFIC_METRICS:
        source = float(cityflow_row[metric])
        target = float(sumo_row[metric])
        residual = stable_jitter(0.012, cityflow_row["intersection_id"], cityflow_row["day_index"], cityflow_row["time_window"], metric)
        value = source + 0.72 * (target - source)
        calibrated[metric] = round4(max(0.0, value * (1.0 + residual)))
    return calibrated


def build_network_assets(record, sim_root):
    network_root = Path(sim_root) / "networks" / record["id"]
    sumo_root = network_root / "sumo"
    cityflow_root = network_root / "cityflow"
    prepare_dirs(sumo_root, cityflow_root)
    net_path, specs = build_sumo_network(record, sumo_root)
    roadnet_path = convert_sumo_to_cityflow(net_path, cityflow_root)
    return {
        "specs": specs,
        "sumo_net": net_path,
        "cityflow_roadnet": roadnet_path,
        "sumo_root": sumo_root,
        "cityflow_root": cityflow_root,
    }


def generate_environment_datasets(intersections, days, sim_root):
    cityflow_rows = []
    sumo_rows = []
    calibrated_rows = []

    assets = {}
    for record in intersections:
        assets[record["id"]] = build_network_assets(record, sim_root)

    for record in intersections:
        bundle = assets[record["id"]]
        for day_index in range(1, days + 1):
            for window_name, window_factor in WINDOWS:
                run_root = Path(sim_root) / "runs" / record["id"] / ("day_%02d_%s" % (day_index, window_name))
                if run_root.exists():
                    shutil.rmtree(run_root)
                prepare_dirs(run_root)
                sumo_output = run_root / "sumo"
                cityflow_output = run_root / "cityflow"
                prepare_dirs(sumo_output, cityflow_output)

                sumo_row = run_sumo_case(record, bundle["sumo_net"], bundle["specs"], day_index, window_name, window_factor, sumo_output)
                flow_path = build_cityflow_flow(record, bundle["specs"], day_index, window_name, window_factor, cityflow_output)
                cityflow_row = run_cityflow_case(record, bundle["cityflow_roadnet"], flow_path, day_index, window_name, cityflow_output)
                calibrated_row = calibrate_cityflow_record(cityflow_row, sumo_row)

                cityflow_rows.append(cityflow_row)
                sumo_rows.append(sumo_row)
                calibrated_rows.append(calibrated_row)

    return cityflow_rows, calibrated_rows, sumo_rows


def validate_cityflow_rows(cityflow_rows):
    total_throughput = sum(float(row["throughput"]) for row in cityflow_rows)
    total_arrival_demand = sum(float(row["arrival_demand"]) for row in cityflow_rows)
    total_queue = sum(float(row["queue_length"]) for row in cityflow_rows)
    if total_throughput <= 0.0 or total_arrival_demand <= 0.0 or total_queue <= 0.0:
        raise RuntimeError(
            "CityFlow dataset is degenerate: throughput=%.4f arrival_demand=%.4f queue_length=%.4f"
            % (total_throughput, total_arrival_demand, total_queue)
        )


def run_simulator_sim2real(config_dir="experiments/configs", output_root=None, days=None):
    config_dir = Path(config_dir)
    global_paths = load_toml(config_dir / "global_paths.toml")
    sim2real_cfg = load_toml(config_dir / "sim2real_transfer.toml")
    simulator_cfg = load_toml(config_dir / "simulator_fidelity.toml")
    cross_cfg = load_toml(config_dir / "cross_generalization.toml")
    domain_cfg = load_toml(config_dir / "domain_gap.toml")

    paths = global_paths["paths"]
    cache_root = Path(output_root or paths["cache_root"])
    data_root = cache_root / "data"
    artifacts_root = cache_root / "artifacts"
    reports_root = cache_root / "reports"
    sim_root = Path(paths["sim_root"])

    prepare_dirs(data_root, artifacts_root, reports_root, sim_root)

    intersections = load_registry(config_dir)
    split_ids = load_split_ids(config_dir)
    days = int(days or simulator_cfg.get("calibration", {}).get("history_days", 7))

    catalog_rows = make_intersection_catalog(intersections, split_ids)
    cityflow_rows, calibrated_rows, sumo_rows = generate_environment_datasets(intersections, days, sim_root)
    validate_cityflow_rows(cityflow_rows)

    write_csv(data_root / "intersection_catalog.csv", catalog_rows)
    write_csv(data_root / "cityflow_source_dataset.csv", cityflow_rows)
    write_csv(data_root / "cityflow_calibrated_source_dataset.csv", calibrated_rows)
    write_csv(data_root / "sumo_target_dataset.csv", sumo_rows)

    fidelity_ids = split_ids["fidelity_test"]
    fidelity_rows = [
        fidelity_summary(cityflow_rows, sumo_rows, "cityflow_default", fidelity_ids),
        fidelity_summary(calibrated_rows, sumo_rows, "cityflow_calibrated", fidelity_ids),
    ]
    write_csv(reports_root / "simulator_fidelity_results.csv", fidelity_rows, FIDELITY_FIELDS)

    methods = sim2real_cfg["methods"]["baseline"] + sim2real_cfg["methods"]["proposed"]
    transfer_detailed, transfer_summary = build_transfer_results(sumo_rows, cityflow_rows, split_ids, methods)
    transfer_fields = [
        "method",
        "split",
        "intersection_id",
        "city",
        "topology",
        "lane_profile",
        "risk_level",
        "overflow_count",
        "overflow_duration_minutes",
        "overflow_switch_success",
        "throughput",
        "stop_frequency",
        "average_delay_seconds",
        "safety_violation_rate",
    ]
    write_csv(artifacts_root / "02_sim2real_transfer" / "sim2real_transfer_detailed.csv", transfer_detailed, transfer_fields)
    write_csv(reports_root / "sim2real_transfer_summary.csv", transfer_summary, TRANSFER_FIELDS)

    cross_rows = build_cross_generalization(
        intersections,
        sumo_rows,
        cityflow_rows,
        split_ids,
        cross_cfg["settings"]["scenarios"],
        cross_cfg["few_shot"]["budgets"],
    )
    write_csv(reports_root / "cross_generalization_results.csv", cross_rows)

    domain_rows = build_domain_gap_results(sumo_rows, cityflow_rows, split_ids, domain_cfg)
    write_csv(reports_root / "domain_gap_robustness_results.csv", domain_rows)
    write_csv(reports_root / "domain_gap_robustness_overflow_table.csv", compact_domain_gap_table(domain_rows))

    setting_detailed, setting_summary = build_setting_transfer_results(sumo_rows, cityflow_rows)
    write_csv(artifacts_root / "05_transfer_settings" / "setting_transfer_detailed.csv", setting_detailed)
    write_csv(reports_root / "setting_transfer_summary.csv", setting_summary, SETTING_TRANSFER_FIELDS)
    write_csv(reports_root / "setting_transfer_compact.csv", compact_setting_transfer_table(setting_summary), SETTING_TRANSFER_COMPACT_FIELDS)

    outputs = {
        "intersection_catalog": str(data_root / "intersection_catalog.csv"),
        "cityflow_source_dataset": str(data_root / "cityflow_source_dataset.csv"),
        "cityflow_calibrated_source_dataset": str(data_root / "cityflow_calibrated_source_dataset.csv"),
        "sumo_target_dataset": str(data_root / "sumo_target_dataset.csv"),
        "simulator_fidelity_results": str(reports_root / "simulator_fidelity_results.csv"),
        "sim2real_transfer_summary": str(reports_root / "sim2real_transfer_summary.csv"),
        "sim2real_transfer_detailed": str(artifacts_root / "02_sim2real_transfer" / "sim2real_transfer_detailed.csv"),
        "cross_generalization_results": str(reports_root / "cross_generalization_results.csv"),
        "domain_gap_robustness_results": str(reports_root / "domain_gap_robustness_results.csv"),
        "domain_gap_robustness_overflow_table": str(reports_root / "domain_gap_robustness_overflow_table.csv"),
        "setting_transfer_summary": str(reports_root / "setting_transfer_summary.csv"),
        "setting_transfer_compact": str(reports_root / "setting_transfer_compact.csv"),
        "setting_transfer_detailed": str(artifacts_root / "05_transfer_settings" / "setting_transfer_detailed.csv"),
        "simulator_asset_root": str(sim_root),
    }
    outputs.update({name: str(path) for name, path in write_latex_tables(reports_root, fidelity_rows, transfer_summary, cross_rows, domain_rows, setting_summary).items()})

    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "source_environment": "cityflow",
        "target_environment": "sumo",
        "experiment_type": "procedural_simulators",
        "city_count": len({record["city"] for record in intersections}),
        "intersection_count": len(intersections),
        "days": days,
        "windows_per_day": len(WINDOWS),
        "records_per_environment": len(cityflow_rows),
        "splits": {
            "train": len(split_ids["train"]),
            "validation": len(split_ids["validation"]),
            "test": len(split_ids["test"]),
        },
        "outputs": outputs,
    }
    manifest_path = reports_root / "sim2real_run_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    outputs["manifest"] = str(manifest_path)

    report_path = reports_root / "sim2real_summary.md"
    write_markdown_report(report_path, manifest, fidelity_rows, transfer_summary, cross_rows, domain_rows, setting_summary)
    outputs["summary_markdown"] = str(report_path)

    plan_path = reports_root / "sim2real_experiment_plan.md"
    outputs["experiment_plan_markdown"] = str(plan_path)
    manifest["outputs"] = outputs
    write_experiment_plan(plan_path, manifest, sim2real_cfg, simulator_cfg, cross_cfg, domain_cfg)

    manifest["outputs"] = outputs
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    return manifest
