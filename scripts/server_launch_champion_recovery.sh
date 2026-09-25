#!/usr/bin/env bash
# Launch the champion_recovery training run on the training server.
#
# Self-contained: run on the server. Expects:
#   - weights/champion_v1.pt          (scp'd from the Mac, see reports/SERVER_HANDOFF.md)
#   - data/processed/yolo_seg_hn999/  (built by scripts/server_build_hn999.sh)
#
# Usage:
#   bash scripts/server_launch_champion_recovery.sh
set -euo pipefail

REPO="${REPO:-$HOME/car_defect_detection}"
CONFIG="${CONFIG:-configs/train/stage2_v2/champion_recovery.yaml}"
RUN_NAME="${RUN_NAME:-champion_recovery}"

fail() { echo "[error] $*" >&2; exit 1; }

# --- Preflight ---
CONDA_BASE="$(conda info --base 2>/dev/null || true)"
[ -n "$CONDA_BASE" ] || fail "conda not found"
# shellcheck disable=SC1091
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate car_defect || fail "conda activate car_defect failed"

cd "$REPO" || fail "REPO not found: $REPO"

[ -f "weights/champion_v1.pt" ] || fail \
  "weights/champion_v1.pt missing. On the Mac run: scp runs/segment/seesaw_surgical_objectness-26/weights/best.pt <server>:~/car_defect_detection/weights/champion_v1.pt"
[ -f "data/processed/yolo_seg_hn999/data.yaml" ] || fail \
  "data/processed/yolo_seg_hn999/data.yaml missing. On the server run: bash scripts/server_build_hn999.sh"
[ -f "$CONFIG" ] || fail "config missing: $CONFIG (run: git pull --ff-only)"

# Refuse to launch if a training process for this config/run is already alive
existing="$(pgrep -f "train\.py --config ${CONFIG}" || true)"
[ -z "$existing" ] && existing="$(pgrep -f "train\.py.*${RUN_NAME}" || true)"
if [ -n "$existing" ]; then
  echo "[refuse] training already running (PID: $existing)" >&2
  exit 1
fi

# --- Launch in background ---
LOG="$REPO/logs/train_${RUN_NAME}_$(date +%Y%m%d_%H%M%S).log"
mkdir -p "$REPO/logs"
nohup python src/train/train.py --config "$CONFIG" > "$LOG" 2>&1 &
echo $! > "$REPO/logs/train_${RUN_NAME}.pid"
echo "[launch] PID $(cat "$REPO/logs/train_${RUN_NAME}.pid") log: $LOG"

# --- Post-launch sanity (warn only — never kill the run) ---
sleep 45
echo "=== tail -n 60 $LOG ==="
tail -n 60 "$LOG"

warn=0
check() {
  if grep -qF "$1" "$LOG"; then
    echo "[ok]   found: $1"
  else
    echo "[warn] NOT found in log yet: $1" >&2
    warn=1
  fi
}
check "model=weights/champion_v1.pt"
check "data=data/processed/yolo_seg_hn999/data.yaml"
check "seesaw_p=0.6"
check "imgsz=1024"
check "epochs=40"

if grep -qF "[cv_obj] level" "$LOG"; then
  if grep -F "[cv_obj] level" "$LOG" | grep -qF -- "-2.0000"; then
    echo "[warn] cv_obj bias line shows init value -2.0000 — checkpoint may lack cv_obj" >&2
    warn=1
  else
    echo "[ok]   cv_obj bias line present with non-init values"
  fi
else
  echo "[warn] cv_obj bias line not in log yet (head replacement may still be running)" >&2
  warn=1
fi

[ "$warn" -eq 0 ] || echo "[warn] some expected log lines missing — check $LOG manually (run NOT killed)" >&2

echo ""
echo "Monitor with:  tail -f $LOG"
