This directory holds the experiment environment scaffold for the sim-to-real
revision proposed in `latex/TODO.md`.

Layout:

- `configs/`: experiment settings and runtime defaults.
- `overflowlight_exp/`: Python helpers for split generation and experiment planning.
- `tools/`: config validation utilities.

The current scaffold supports:

- canonical registry and split generation for the 43 deployed intersections;
- experiment planning manifests for the four studies in `latex/TODO.md`;
- procedurally generated CityFlow-to-SUMO simulator experiments for the 43 intersections;
- Slurm entrypoints for split preparation and plan generation.

The simulation runner treats CityFlow as the source simulation environment and
SUMO as the target real-domain surrogate. Because raw roadnets and field logs
are not present in this workspace, it procedurally builds 43 single-intersection
network bundles from the registry metadata, runs both simulators, and then
derives the comparison datasets and summary tables from those simulator outputs.

LUMI usage:

1. Build the container-backed virtual environment:

   `sbatch --wait scripts/slurm/bootstrap_venv.sbatch`

2. Validate and materialize the experiment directories on a compute node:

   `sbatch --wait scripts/slurm/validate_experiment_env.sbatch`

3. Build split manifests:

   `sbatch --wait scripts/slurm/prepare_splits.sbatch`

4. Build experiment planning manifests:

   `sbatch --wait scripts/slurm/plan_experiments.sbatch`

5. Run the CityFlow-to-SUMO simulator experiment and produce tables:

   `sbatch --wait scripts/slurm/simulate_s2r.sbatch`

All cache-heavy outputs are routed to:

`/scratch/project_462001050/cache/overflowlight_s2r`
