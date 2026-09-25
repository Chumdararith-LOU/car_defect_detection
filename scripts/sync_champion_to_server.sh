#!/usr/bin/env bash
# Copy the champion checkpoint to the training server and verify checksums.
#
# Usage:
#   CAR_SERVER=myserver scripts/sync_champion_to_server.sh
#
# CAR_SERVER is an ssh alias (see ~/.ssh/config). Not hardcoded on purpose.
set -euo pipefail

SERVER="${CAR_SERVER:?set CAR_SERVER to the ssh alias of the training server}"
SRC="runs/segment/seesaw_surgical_objectness-26/weights/best.pt"
DEST_DIR="weights"
DEST_NAME="champion_v1.pt"

cd "$(dirname "$0")/.."

[ -f "$SRC" ] || { echo "[error] $SRC not found" >&2; exit 1; }

local_sha() { command -v sha256sum >/dev/null && sha256sum "$1" || shasum -a 256 "$1"; }

echo "[sha256] local before: $(local_sha "$SRC")"

ssh "$SERVER" "mkdir -p ~/car_defect_detection/${DEST_DIR}"
scp "$SRC" "$SERVER:~/car_defect_detection/${DEST_DIR}/${DEST_NAME}"

echo "[sha256] remote after:  $(ssh "$SERVER" "sha256sum ~/car_defect_detection/${DEST_DIR}/${DEST_NAME}")"
echo "[done] $SRC -> $SERVER:~/car_defect_detection/${DEST_DIR}/${DEST_NAME}"
