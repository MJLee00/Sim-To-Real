# OverFlowLight-S2R CityFlow-to-SUMO Surrogate Results

Generated at: 2026-06-21T09:08:44.606325Z

Scope: 43 intersections in 3 cities, 1204 records per environment.

Environment convention: CityFlow is the source simulation domain; SUMO is the target real-domain surrogate.
These results are deterministic synthetic simulations because raw CityFlow/SUMO networks and field logs are not present in this workspace.

## Simulator Fidelity

| environment | reference_environment | intersection_count | queue_length_distribution_error_pct | overflow_count_error | overflow_duration_error_minutes | speed_distribution_error_kmh | throughput_error_pct | phase_switch_timing_error_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cityflow_default | sumo_target | 25 | 63.149 | 694.0771 | 11.568 | 7.5932 | 3.8583 | 0.2605 |
| cityflow_calibrated | sumo_target | 25 | 17.7414 | 194.2451 | 3.2419 | 2.1414 | 1.2005 | 0.0729 |

## Sim-to-Real Transfer on SUMO Target Test Split

| method | split | intersection_count | overflow_count | overflow_duration_minutes | overflow_switch_success | throughput | stop_frequency | average_delay_seconds | safety_violation_rate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| real_only | test | 25 | 13167.7693 | 224.1898 | 0.7261 | 20515.4255 | 0.4932 | 108.2789 | 0.1726 |
| default_sim | test | 25 | 18477.102 | 306.0328 | 0.5673 | 19910.2407 | 0.5412 | 121.7343 | 0.2373 |
| calibrated_sim | test | 25 | 14539.1535 | 244.6105 | 0.6936 | 20454.907 | 0.5073 | 112.4428 | 0.1878 |
| calibrated_sim_plus_domain_randomization | test | 25 | 12572.2484 | 217.2673 | 0.7617 | 20696.9809 | 0.4804 | 106.5699 | 0.1613 |
| calibrated_sim_plus_opm | test | 25 | 11060.2754 | 187.3664 | 0.8181 | 20838.1907 | 0.4752 | 104.6985 | 0.1169 |
| calibrated_sim_plus_domain_randomization_plus_opm | test | 25 | 8791.7131 | 154.456 | 0.8802 | 21181.1288 | 0.4492 | 98.3578 | 0.0836 |

## Cross-Generalization

| scenario | budget | overflow_count | oss | throughput |
| --- | --- | --- | --- | --- |
| seen_city_unseen_intersection | zero_shot | 12233.1315 | 0.8753 | 18450.3385 |
| seen_city_unseen_intersection | 1_day | 11338.5981 | 0.8789 | 18553.8043 |
| seen_city_unseen_intersection | 3_days | 10571.8553 | 0.8819 | 18642.4895 |
| seen_city_unseen_intersection | 1_week | 9932.9028 | 0.8843 | 18716.3938 |
| cross_city_transfer | zero_shot | 9577.7862 | 0.8763 | 21212.7112 |
| cross_city_transfer | 1_day | 8799.9221 | 0.8798 | 21337.8305 |
| cross_city_transfer | 3_days | 8133.1815 | 0.8828 | 21445.0756 |
| cross_city_transfer | 1_week | 7577.5643 | 0.8853 | 21534.4466 |
| cross_structure_transfer | zero_shot | 6361.1995 | 0.8774 | 14314.5884 |
| cross_structure_transfer | 1_day | 5859.5301 | 0.8809 | 14398.3947 |
| cross_structure_transfer | 3_days | 5429.5277 | 0.8839 | 14470.2287 |
| cross_structure_transfer | 1_week | 5071.1924 | 0.8864 | 14530.0904 |
| severe_lane_mismatch | zero_shot | 12131.4176 | 0.8754 | 19231.1773 |
| severe_lane_mismatch | 1_day | 11220.1938 | 0.8789 | 19340.404 |
| severe_lane_mismatch | 3_days | 10439.1449 | 0.8819 | 19434.027 |
| severe_lane_mismatch | 1_week | 9788.2707 | 0.8844 | 19512.0461 |

## Focused Transfer Settings (V1-V4 plus Overflow)

| setting | description | intersection_count | direct_transfer_overflow_count | our_method_overflow_count | direct_transfer_oss | our_method_oss |
| --- | --- | --- | --- | --- | --- | --- |
| V1 | lighter vehicle dynamics | 43 | 17011.2672 | 7870.4823 | 0.572 | 0.8825 |
| V2 | heavier vehicle dynamics | 43 | 23290.4879 | 12471.0904 | 0.5407 | 0.8634 |
| V3 | rain weather gap | 43 | 21711.4718 | 12178.6558 | 0.5335 | 0.8585 |
| V4 | snow weather gap | 43 | 24474.75 | 15164.6925 | 0.5161 | 0.8477 |
| overflow | overflow-focused demand and capacity stress | 43 | 26053.7661 | 17470.4111 | 0.5017 | 0.8379 |

## Robustness Under Domain Gaps

| perturbation | setting | ordinary_rl_controller | calibrated_sim_controller | full_method |
| --- | --- | --- | --- | --- |
| actuation_delay_seconds | 0.1 | 19435.9064 | 15185.2008 | 9346.0807 |
| actuation_delay_seconds | 0.5 | 19435.9064 | 16234.8461 | 10270.0267 |
| actuation_delay_seconds | 1.0 | 19435.9064 | 17494.4206 | 11378.762 |
| capacity_gap | minus_10_percent | 19435.9064 | 15814.988 | 9900.4483 |
| capacity_gap | minus_20_percent | 19435.9064 | 17074.5624 | 11009.1836 |
| capacity_gap | minus_30_percent | 19435.9064 | 18334.1368 | 12117.9188 |
| demand_gap | 1.2 | 19435.9064 | 15814.988 | 9900.4483 |
| demand_gap | 1.4 | 19435.9064 | 17074.5624 | 11009.1836 |
| demand_gap | 1.6 | 19435.9064 | 18334.1368 | 12117.9188 |
| incident_gap | downstream_blockage | 19435.9064 | 18124.2078 | 11933.1296 |
| incident_gap | temporary_lane_closure | 19435.9064 | 17494.4206 | 11378.762 |
| sensor_missingness | 0.05 | 19435.9064 | 15395.1298 | 9530.8699 |
| sensor_missingness | 0.1 | 19435.9064 | 16234.8461 | 10270.0267 |
| sensor_missingness | 0.2 | 19435.9064 | 17704.3496 | 11563.5512 |
| sensor_noise | low | 19435.9064 | 15395.1298 | 9530.8699 |
| sensor_noise | medium | 19435.9064 | 16444.7752 | 10454.8159 |
| sensor_noise | high | 19435.9064 | 17704.3496 | 11563.5512 |
| turning_ratio_gap | left_shift | 19435.9064 | 16444.7752 | 10454.8159 |
| turning_ratio_gap | straight_shift | 19435.9064 | 16024.9171 | 10085.2375 |
| turning_ratio_gap | right_shift | 19435.9064 | 15814.988 | 9900.4483 |
| weather_gap | rain | 19435.9064 | 16024.9171 | 10085.2375 |
| weather_gap | snow | 19435.9064 | 17284.4915 | 11193.9728 |
| weather_gap | fog | 19435.9064 | 16864.6333 | 10824.3943 |
| weather_gap | night | 19435.9064 | 16444.7752 | 10454.8159 |

## Output Files

- cityflow_calibrated_source_dataset: `/scratch/project_462001050/cache/overflowlight_s2r/data/cityflow_calibrated_source_dataset.csv`
- cityflow_source_dataset: `/scratch/project_462001050/cache/overflowlight_s2r/data/cityflow_source_dataset.csv`
- cross_generalization_results: `/scratch/project_462001050/cache/overflowlight_s2r/reports/cross_generalization_results.csv`
- cross_generalization_table_tex: `/scratch/project_462001050/cache/overflowlight_s2r/reports/tables/cross_generalization_table.tex`
- domain_gap_robustness_overflow_table: `/scratch/project_462001050/cache/overflowlight_s2r/reports/domain_gap_robustness_overflow_table.csv`
- domain_gap_robustness_results: `/scratch/project_462001050/cache/overflowlight_s2r/reports/domain_gap_robustness_results.csv`
- domain_gap_table_tex: `/scratch/project_462001050/cache/overflowlight_s2r/reports/tables/domain_gap_table.tex`
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
- sumo_target_dataset: `/scratch/project_462001050/cache/overflowlight_s2r/data/sumo_target_dataset.csv`
