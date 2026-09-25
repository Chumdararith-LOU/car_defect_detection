#!/usr/bin/env bash
# Build data/processed/yolo_seg_hn999 on the training server.
#
# Self-contained: run on the server, assumes nothing is running on the Mac.
# Idempotent: safe to re-run (rsync --delete rebuilds the copy, the inject
# script deletes prior cneg__ files before re-injecting, sanitize is idempotent).
#
# Usage:
#   bash scripts/server_build_hn999.sh
#   DEBUG=1 bash scripts/server_build_hn999.sh   # trace every command
set -euo pipefail

REPO="${REPO:-$HOME/car_defect_detection}"
SRC_DATASET="${SRC_DATASET:-$REPO/data/processed/yolo_seg}"
DST_DATASET="${DST_DATASET:-$REPO/data/processed/yolo_seg_hn999}"
CLEAN_POOL="${CLEAN_POOL:-$REPO/data/processed/clean_cars}"
NEG_TARGET=999

[ "${DEBUG:-0}" = "1" ] && set -x

fail() { echo "[error] $*" >&2; exit 1; }

# --- Preflight ---
CONDA_BASE="$(conda info --base 2>/dev/null || true)"
[ -n "$CONDA_BASE" ] || fail "conda not found"
# shellcheck disable=SC1091
source "${CONDA_BASE}/etc/profile.d/conda.sh"
conda activate car_defect || fail "conda activate car_defect failed"

[ -d "$REPO" ] || fail "REPO not found: $REPO"
[ -f "$SRC_DATASET/data.yaml" ] || fail "source dataset missing: $SRC_DATASET/data.yaml"
[ -d "$CLEAN_POOL/images/clean_train" ] || fail "clean pool missing: $CLEAN_POOL/images/clean_train/"
[ "$CLEAN_POOL" = "$REPO/data/processed/clean_cars" ] || \
  echo "[warn] CLEAN_POOL overridden — inject_clean_negatives.py always reads \$REPO/data/processed/clean_cars"

cd "$REPO"
# Vendored fork (has SeesawBCE) must win over any pip-installed ultralytics
export PYTHONPATH="$REPO/vendor/ultralytics:$REPO${PYTHONPATH:+:$PYTHONPATH}"

echo "[preflight] versions:"
python -c "import sys, torch, ultralytics; print(f'  python      {sys.version.split()[0]}'); print(f'  torch       {torch.__version__}'); print(f'  ultralytics {ultralytics.__version__} ({ultralytics.__file__})')"

# --- 1. Rebuild dataset copy from source ---
echo "[build] rsync $SRC_DATASET/ -> $DST_DATASET/"
mkdir -p "$DST_DATASET"
rsync -a --delete "$SRC_DATASET/" "$DST_DATASET/"

# --- 2. Fix data.yaml ---
# Drop 'path:' — ultralytics then resolves train/val/test relative to this
# yaml's own directory, which is correct on the server.
# 7-class taxonomy: class 0 is broken_part, not broken_lamp.
python - "$DST_DATASET/data.yaml" <<'EOF'
import sys
from pathlib import Path
p = Path(sys.argv[1])
lines = [l for l in p.read_text().splitlines() if not l.startswith("path:")]
lines = [l.replace("0: broken_lamp", "0: broken_part") for l in lines]
p.write_text("\n".join(lines) + "\n")
EOF
grep -q "broken_part" "$DST_DATASET/data.yaml" || fail "class 0 is not broken_part in $DST_DATASET/data.yaml"

# --- 3. Inject clean negatives (iterate ratio upward until target or pool exhausted) ---
# --target takes an absolute path: pathlib join discards the script's own
# data/processed prefix when the right-hand side is absolute.
prev=0
injected=0
for ratio in 0.20 0.25 0.30 0.35; do
  python src/data/inject_clean_negatives.py --target "$DST_DATASET" --neg-ratio "$ratio"
  injected=$(python -c "import json; print(json.load(open('$DST_DATASET/.injected_clean.json'))['injected_clean_images'])")
  echo "[inject] ratio=$ratio injected=$injected target=$NEG_TARGET"
  [ "$injected" -ge "$NEG_TARGET" ] && break
  [ "$injected" -le "$prev" ] && { echo "[warn] clean pool exhausted at $injected (< $NEG_TARGET)"; break; }
  prev=$injected
done
[ "$injected" -ge "$NEG_TARGET" ] || echo "[warn] only $injected clean negatives injected (target $NEG_TARGET)"

# --- 4. Sanitize zero-area instances (fixed --min-points 3 guard) ---
python src/data/sanitize_zero_area.py --root "$DST_DATASET" --inplace --report "$REPO/reports/zero_area_report_hn999_server.json"
dropped=$(python -c "import json; r=json.load(open('$REPO/reports/zero_area_report_hn999_server.json')); print(sum(v['dropped'] for v in r.values()))")
echo "[sanitize] dropped=$dropped"
if [ "$dropped" -gt 700 ]; then
  echo "!!! SANITIZE DROPPED $dropped INSTANCES (> 700). The drop criterion is likely wrong. Aborting." >&2
  exit 1
fi

# --- 5. Verify dataset resolution points at the built dataset ---
python - "$DST_DATASET" <<'EOF'
import sys
from pathlib import Path
from ultralytics.data.utils import check_det_dataset

dst = Path(sys.argv[1]).resolve()
d = check_det_dataset(str(dst / "data.yaml"))
train = Path(d["train"]).resolve()
print(f"[verify] resolved train: {train}")
if not str(train).startswith(str(dst) + "/"):
    print(f"[error] train resolves OUTSIDE the built dataset: {train}", file=sys.stderr)
    sys.exit(1)
print("[verify] OK: resolves inside the built dataset")
EOF

# --- 6. Final stats ---
python - "$DST_DATASET" <<'EOF'
import json, sys
from collections import Counter
from pathlib import Path
import yaml

dst = Path(sys.argv[1])
names = yaml.safe_load((dst / "data.yaml").read_text()).get("names", {})
if isinstance(names, list):
    names = {i: n for i, n in enumerate(names)}
imgs = list((dst / "images/train").iterdir())
pos = sum(1 for f in imgs if not f.name.startswith("cneg__"))
cneg = sum(1 for f in imgs if f.name.startswith("cneg__"))
cls = Counter()
for lbl in (dst / "labels/train").glob("*.txt"):
    for line in lbl.read_text().splitlines():
        if line.strip():
            cls[line.split()[0]] += 1
print(f"\n=== final stats: {dst} ===")
print(f"positive images : {pos}")
print(f"clean negatives : {cneg}")
print(f"total train imgs: {pos + cneg}")
print("class distribution (train instances):")
for k in sorted(cls, key=int):
    print(f"  {k} ({names.get(k, names.get(int(k), '?'))}): {cls[k]}")
print("\n.injected_clean.json:")
print((dst / ".injected_clean.json").read_text())
EOF

echo "[done] $DST_DATASET built"
