# CityFlow-to-SUMO Sim-to-Real Experiment Plan

Generated at: 2026-06-21T09:08:44.606325Z

## Environment Mapping

- Source simulator: CityFlow
- Target real-domain surrogate: SUMO
- Intersections: 43 across 3 cities
- Synthetic horizon: 7 days x 4 windows per day
- Splits: train=16, validation=2, test=25

## Experiment 1: Simulator Fidelity

Compare CityFlow source traces against SUMO target traces on the fidelity test split.

- Candidate environments: cityflow_default, cityflow_calibrated
- Reference environment: sumo_target
- Metrics: queue_length_distribution_error, overflow_count_error, overflow_duration_error, speed_distribution_error, throughput_error, phase_switch_timing_error

## Experiment 2: Sim-to-Real Transfer

Train or tune controller variants in the CityFlow source domain and evaluate transfer on the SUMO target test split.

- Methods: real_only, default_sim, calibrated_sim, calibrated_sim_plus_domain_randomization, calibrated_sim_plus_opm, calibrated_sim_plus_domain_randomization_plus_opm
- Selection metric: overflow_switch_success
- Metrics: overflow_count, overflow_duration, overflow_switch_success, throughput, stop_frequency, average_delay, safety_violation_rate

## Experiment 3: Cross-Generalization

Evaluate the full CityFlow-to-SUMO method on held-out intersections, cross-city targets, topology shifts, and severe lane mismatch.

- Scenarios: seen_city_unseen_intersection, cross_city_transfer, cross_structure_transfer, severe_lane_mismatch
- Calibration budgets: zero_shot, 1_day, 3_days, 1_week

## Focused Transfer Slice

Compare direct controller transfer against the full OverFlowLight transfer stack under UGAT-style V1-V4 conditions plus an overflow stress setting.

- Direct transfer: default_sim
- Proposed transfer: calibrated_sim_plus_domain_randomization_plus_opm
- Setting map: V1=lighter vehicle dynamics, V2=heavier vehicle dynamics, V3=rain weather gap, V4=snow weather gap, overflow=overflow-focused demand and capacity stress

## Experiment 4: Domain-Gap Robustness

Stress test the transferred controller under traffic, sensing, weather, incident, capacity, and actuation perturbations.

- Perturbation families: actuation_delay_seconds, capacity_gap, demand_gap, incident_gap, sensor_missingness, sensor_noise, turning_ratio_gap, weather_gap
- Reference methods: ordinary_rl_controller, calibrated_sim_controller, calibrated_sim_plus_domain_randomization_plus_opm

## Result Artifacts

- cityflow_calibrated_source_dataset: `/scratch/project_462001050/cache/overflowlight_s2r/data/cityflow_calibrated_source_dataset.csv`
- cityflow_source_dataset: `/scratch/project_462001050/cache/overflowlight_s2r/data/cityflow_source_dataset.csv`
- cross_generalization_results: `/scratch/project_462001050/cache/overflowlight_s2r/reports/cross_generalization_results.csv`
- cross_generalization_table_tex: `/scratch/project_462001050/cache/overflowlight_s2r/reports/tables/cross_generalization_table.tex`
- domain_gap_robustness_overflow_table: `/scratch/project_462001050/cache/overflowlight_s2r/reports/domain_gap_robustness_overflow_table.csv`
- domain_gap_robustness_results: `/scratch/project_462001050/cache/overflowlight_s2r/reports/domain_gap_robustness_results.csv`
- domain_gap_table_tex: `/scratch/project_462001050/cache/overflowlight_s2r/reports/tables/domain_gap_table.tex`
- experiment_plan_markdown: `/scratch/project_462001050/cache/overflowlight_s2r/reports/sim2real_experiment_plan.md`
- intersection_catalog: `/scratch/project_462001050/cache/overflowlight_s2r/data/intersection_catalog.csv`
- manifest: `/scratch/project_462001050/cache/overflowlight_s2r/reports/sim2real_run_manifest.json`
- setting_transfer_compact: `/scratch/project_462001050/cache/overflowlight_s2r/reports/setting_transfer_compact.csv`
- setting_transfer_detailed: `/scratch/project_462001050/cache/overflowlight_s2r/artifacts/05_transfer_settings/setting_transfer_detailed.csv`
- setting_transfer_summary: `/scratch/project_462001050/cache/overflowlight_s2r/reports/setting_transfer_summary.csv`
- setting_transfer_table_tex: `/scratch/project_462001050/cache/overflowlight_s2r/reports/tables/setting_transfer_table.tex`
- sim2real_transfer_detailed: `/scratch/project_462001050/cache/overflowlight_s2r/artifacts/02_sim2real_transfer/sim2real_transfer_detailed.csv`
- sim2real_transfer_summary: `/scratch/project_462001050/cache/overflowlight_s2r/reports/sim2real_transfer_summary.csv`
- sim2real_transfer_table_tex: `/scratch/project_462001050/cache/overflowlight_s2r/reports/tables/sim2real_transfer_table.tex`
- simulator_asset_root: `/scratch/project_462001050/cache/overflowlight_s2r/simulators`
- simulator_fidelity_results: `/scratch/project_462001050/cache/overflowlight_s2r/reports/simulator_fidelity_results.csv`
- simulator_fidelity_table_tex: `/scratch/project_462001050/cache/overflowlight_s2r/reports/tables/simulator_fidelity_table.tex`
- summary_markdown: `/scratch/project_462001050/cache/overflowlight_s2r/reports/sim2real_summary.md`
- sumo_target_dataset: `/scratch/project_462001050/cache/overflowlight_s2r/data/sumo_target_dataset.csv`
