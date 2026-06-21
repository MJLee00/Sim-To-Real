#!/usr/bin/env bash
set -euo pipefail

LUMI_SINGULARITY_BIN="${LUMI_SINGULARITY_BIN:-/usr/bin/singularity}"
SCRATCH_CACHE_ROOT="${SCRATCH_CACHE_ROOT:-/scratch/project_462001050/cache/overflowlight_s2r}"

lumi_prepare_modules() {
    module --force purge
    module use /appl/local/laifs/modules
    module load lumi-aif-singularity-bindings
}

lumi_default_sif() {
    if [[ -n "${LUMI_SIF:-}" ]]; then
        printf '%s\n' "${LUMI_SIF}"
        return
    fi

    if [[ -f /appl/local/laifs/containers/lumi-multitorch-latest.sif ]]; then
        printf '%s\n' "/appl/local/laifs/containers/lumi-multitorch-latest.sif"
        return
    fi

    printf '%s\n' "/appl/local/laifs/containers/lumi-multitorch-u24r70f21m50t210-20260415_130625/lumi-multitorch-full-u24r70f21m50t210-20260415_130625.sif"
}

lumi_prepare_miopen_cache() {
    local job_tmp
    job_tmp="${TMPDIR:-${SCRATCH_CACHE_ROOT}/tmp/${SLURM_JOB_ID:-manual}}"
    mkdir -p "${job_tmp}/miopen/cache" "${job_tmp}/miopen/config"
    export MIOPEN_CUSTOM_CACHE_DIR="${job_tmp}/miopen/cache"
    export MIOPEN_USER_DB="${job_tmp}/miopen/config"
}

lumi_prepare_rccl_env() {
    export NCCL_SOCKET_IFNAME="hsn0,hsn1,hsn2,hsn3"
    export NCCL_NET_GDR_LEVEL="PHB"
}

lumi_configure_project_paths() {
    PROJECT_ROOT="$(cd "${PROJECT_ROOT:-${SLURM_SUBMIT_DIR:-$PWD}}" && pwd)"
    export PROJECT_ROOT

    export XDG_CACHE_HOME="${XDG_CACHE_HOME:-${SCRATCH_CACHE_ROOT}/xdg}"
    export HF_HOME="${HF_HOME:-${SCRATCH_CACHE_ROOT}/huggingface}"
    export HUGGINGFACE_HUB_CACHE="${HUGGINGFACE_HUB_CACHE:-${HF_HOME}/hub}"
    export TRANSFORMERS_CACHE="${TRANSFORMERS_CACHE:-${HF_HOME}/transformers}"
    export TORCH_HOME="${TORCH_HOME:-${SCRATCH_CACHE_ROOT}/torch}"
    export PIP_CACHE_DIR="${PIP_CACHE_DIR:-${SCRATCH_CACHE_ROOT}/pip}"
    export SINGULARITY_CACHEDIR="${SINGULARITY_CACHEDIR:-${SCRATCH_CACHE_ROOT}/singularity}"
    export MPLCONFIGDIR="${MPLCONFIGDIR:-${SCRATCH_CACHE_ROOT}/matplotlib}"
    export TMPDIR="${TMPDIR:-${SCRATCH_CACHE_ROOT}/tmp/${SLURM_JOB_ID:-manual}}"

    mkdir -p \
        "${SCRATCH_CACHE_ROOT}" \
        "${XDG_CACHE_HOME}" \
        "${HF_HOME}" \
        "${HUGGINGFACE_HUB_CACHE}" \
        "${TRANSFORMERS_CACHE}" \
        "${TORCH_HOME}" \
        "${PIP_CACHE_DIR}" \
        "${SINGULARITY_CACHEDIR}" \
        "${MPLCONFIGDIR}" \
        "${TMPDIR}"
}

lumi_prepare_venv_mount() {
    local sqsh_path="${PROJECT_ROOT}/.venv.sqsh"
    local dir_path="${PROJECT_ROOT}/.venv"

    unset SINGULARITYENV_PREPEND_PATH || true

    if [[ -f "${sqsh_path}" ]]; then
        export LUMI_VENV_MODE="sqsh"
        export LUMI_VENV_PATH="${sqsh_path}"
        export LUMI_VENV_ACTIVATE="source /user-venv/bin/activate"
        export SINGULARITYENV_PREPEND_PATH="/user-venv/bin"
        return
    fi

    if [[ -d "${dir_path}" ]]; then
        export LUMI_VENV_MODE="dir"
        export LUMI_VENV_PATH="${dir_path}"
        export LUMI_VENV_ACTIVATE="source ${dir_path}/bin/activate"
        return
    fi

    echo "No .venv or .venv.sqsh found under ${PROJECT_ROOT}. Submit scripts/slurm/bootstrap_venv.sbatch first." >&2
    exit 1
}

lumi_prepare_sumo_env() {
    local sumo_root=""
    local candidate

    if [[ -n "${SUMO_HOME:-}" && -d "${SUMO_HOME}" ]]; then
        sumo_root="${SUMO_HOME}"
    else
        for candidate in "${PROJECT_ROOT}/.venv"/lib/python*/site-packages/sumo "/user-venv"/lib/python*/site-packages/sumo; do
            if [[ -d "${candidate}" ]]; then
                sumo_root="${candidate}"
                break
            fi
        done
    fi

    if [[ -z "${sumo_root}" ]]; then
        return 0
    fi

    export SUMO_HOME="${sumo_root}"
    export SINGULARITYENV_SUMO_HOME="${sumo_root}"

    if [[ -d "${sumo_root}/bin" ]]; then
        export PATH="${sumo_root}/bin:${PATH}"
        export SINGULARITYENV_PREPEND_PATH="${sumo_root}/bin:${SINGULARITYENV_PREPEND_PATH:-}"
    fi

    if [[ -d "${sumo_root}/tools" ]]; then
        export PYTHONPATH="${sumo_root}/tools${PYTHONPATH:+:${PYTHONPATH}}"
        export SINGULARITYENV_PYTHONPATH="${sumo_root}/tools${SINGULARITYENV_PYTHONPATH:+:${SINGULARITYENV_PYTHONPATH}}"
    fi
}

lumi_run_container() {
    local container_cmd="$1"
    local sif
    local -a bind_args

    sif="$(lumi_default_sif)"
    bind_args=()

    if [[ "${LUMI_VENV_MODE:-}" == "sqsh" ]]; then
        bind_args=(-B "${LUMI_VENV_PATH}:/user-venv:image-src=/")
    fi

    srun "${LUMI_SINGULARITY_BIN}" run "${bind_args[@]}" "${sif}" bash -lc "${container_cmd}"
}
