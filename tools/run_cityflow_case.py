#!/usr/bin/env python3

import json
import sys
from pathlib import Path

import cityflow


def clamp(value, low, high):
    return min(high, max(low, value))


def round4(value):
    return round(float(value), 4)


def main():
    if len(sys.argv) != 4:
        print("usage: run_cityflow_case.py CONFIG_PATH METRICS_PATH STEPS", file=sys.stderr)
        return 2

    config_path = Path(sys.argv[1]).resolve()
    metrics_path = Path(sys.argv[2]).resolve()
    steps = int(sys.argv[3])
    config = json.loads(config_path.read_text())
    config_dir = Path(config["dir"]).resolve()
    roadnet_path = config_dir / config["roadnetFile"]
    flow_path = config_dir / config["flowFile"]
    missing = [str(path) for path in (config_path, roadnet_path, flow_path) if not path.exists()]
    if missing:
        print("cityflow asset missing: %s" % ", ".join(missing), file=sys.stderr)
        return 1

    engine = cityflow.Engine(config_file=str(config_path), thread_num=1)
    queue_series = []
    waiting_series = []
    speed_series = []
    vehicle_distance_series = []
    vehicle_seen = set()

    for _ in range(steps):
        engine.next_step()
        lane_vehicle_count = engine.get_lane_vehicle_count()
        lane_waiting_count = engine.get_lane_waiting_vehicle_count()
        vehicle_speed = engine.get_vehicle_speed()
        vehicle_distance = engine.get_vehicle_distance()
        vehicle_ids = engine.get_vehicles(include_waiting=True)
        vehicle_seen.update(vehicle_ids)

        queue_series.append(sum(lane_vehicle_count.values()))
        waiting_series.append(sum(lane_waiting_count.values()))
        if vehicle_speed:
            speed_series.append(sum(vehicle_speed.values()) / len(vehicle_speed))
        else:
            speed_series.append(0.0)
        if vehicle_distance:
            vehicle_distance_series.append(sum(vehicle_distance.values()) / len(vehicle_distance))
        else:
            vehicle_distance_series.append(0.0)

    average_travel_time = engine.get_average_travel_time()
    queue_threshold = max(10.0, sum(queue_series) / max(1, len(queue_series)) * 1.15)
    overflow_steps = [value for value in waiting_series if value >= queue_threshold]
    throughput = max(0.0, len(vehicle_seen) - waiting_series[-1])
    queue_length = sum(queue_series) / max(1, len(queue_series)) * 2.8
    overflow_count = len(overflow_steps)
    overflow_duration_seconds = float(overflow_count)
    speed_kmh = (sum(speed_series) / max(1, len(speed_series))) * 3.6
    stop_frequency = sum(waiting_series) / max(1.0, len(waiting_series) * 12.0)
    average_delay_seconds = sum(waiting_series) / max(1, len(waiting_series)) * 1.7
    safety_violation_rate = clamp((overflow_count * 0.01 + queue_length / 260.0), 0.0, 0.22)
    arrival_demand = throughput + waiting_series[-1]
    exit_lane_capacity = max(1.0, throughput / max(1.0, steps / 3600.0))
    phase_switch_timing_error_seconds = 0.18 + abs((queue_threshold - waiting_series[-1]) / max(1.0, queue_threshold)) * 0.2
    if not vehicle_seen and throughput <= 0.0 and arrival_demand <= 0.0:
        print("cityflow produced no traffic; likely invalid flow or asset wiring", file=sys.stderr)
        return 1

    metrics = {
        "arrival_demand": round4(arrival_demand),
        "exit_lane_capacity": round4(exit_lane_capacity),
        "queue_length": round4(queue_length),
        "overflow_count": round4(overflow_count),
        "overflow_duration_seconds": round4(overflow_duration_seconds),
        "speed_kmh": round4(speed_kmh),
        "throughput": round4(throughput),
        "stop_frequency": round4(stop_frequency),
        "average_delay_seconds": round4(average_delay_seconds),
        "safety_violation_rate": round4(safety_violation_rate),
        "phase_switch_timing_error_seconds": round4(phase_switch_timing_error_seconds),
        "average_travel_time": round4(average_travel_time),
        "mean_vehicle_distance": round4(sum(vehicle_distance_series) / max(1, len(vehicle_distance_series))),
    }
    metrics_path.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
