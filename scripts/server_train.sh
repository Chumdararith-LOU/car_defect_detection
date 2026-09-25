#!/usr/bin/env bash
# Launch a Stage 2 training run on the server.
#
# Usage:
#   scripts/server_train.sh <config.yaml> [extra_args] [resume=yes|no] [bg|fg]
#
#   config.yaml   training config (required)
#   extra_args    extra CLI args passed through to train.py (default: none)
#   resume        yes (default) passes --resume; no starts fresh
#   bg|fg         bg = nohup + detach (default: fg)
#
# DRY_RUN=1 prints the resolved command and exits without training.
set -euo pipefail

CONFIG="${1:?usage: server_train.sh <config.yaml> [extra_args] [resume=yes|no] [bg|fg]}"
EXTRA="${2:-}"
RESUME="${3:-yes}"
MODE="${4:-fg}"

cd "$(dirname "$0")/.."

CONDA_BASE="$(conda info --base 2>/dev/null || true)"
if [ -n "${CONDA_BASE}" ]; then
  # shellcheck disable=SC1091
  source "${CONDA_BASE}/etc/profile.d/conda.sh"
fi
conda activate car_defect

if [ "${DRY_RUN:-0}" != "1" ]; then
  git pull --ff-only
fi

read -r PROJECT RUN_NAME < <(python -c "
import sys, yaml
cfg = yaml.safe_load(open(sys.argv[1]))
print(cfg.get('project_name', 'car_defect_detection'), cfg.get('run_name', 'experiment_run'))
" "$CONFIG")

LOCK_DIR="runs/segment/${PROJECT}/${RUN_NAME}"
LOCK="${LOCK_DIR}/.training.lock"
if [ -f "${LOCK}" ]; then
  OLD_PID="$(cat "${LOCK}" 2>/dev/null || true)"
  if [ -n "${OLD_PID}" ] && kill -0 "${OLD_PID}" 2>/dev/null; then
    echo "[refuse] run '${RUN_NAME}' is already training (PID ${OLD_PID}, lock ${LOCK})" >&2
    exit 1
  fi
  echo "[stale] removing stale lock ${LOCK}"
  rm -f "${LOCK}"
fi

LOG="logs/train_$(date +%Y%m%d_%H%M%S).log"
TRAIN_ARGS=(src/train/train.py --config "$CONFIG" ${EXTRA})
if [ "${RESUME}" = "yes" ]; then
  TRAIN_ARGS+=(--resume)
fi

echo "[train] project=${PROJECT} run=${RUN_NAME} resume=${RESUME} mode=${MODE} log=${LOG}"
if [ "${DRY_RUN:-0}" = "1" ]; then
  echo "[dry-run] would run: python ${TRAIN_ARGS[*]}"
  exit 0
fi

mkdir -p "${LOCK_DIR}" logs
echo $$ > "${LOCK}"

if [ "${MODE}" = "bg" ]; then
  nohup python "${TRAIN_ARGS[@]}" > "${LOG}" 2>&1 &
  PID=$!
  echo "${PID}" > "${LOCK}"
  echo "PID: ${PID} (background; log: ${LOG})"
else
  trap 'rm -f "${LOCK}"' EXIT
  python "${TRAIN_ARGS[@]}" 2>&1 | tee "${LOG}" &
  PID=$!
  echo "${PID}" > "${LOCK}"
  echo "PID: ${PID} (foreground; log: ${LOG})"
  wait "${PID}"
fi
