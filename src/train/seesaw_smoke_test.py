import math
import os
import re
import sys
from pathlib import Path

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)
# Vendored fork (has SeesawBCE) must win over any pip-installed ultralytics
_VENDOR = os.path.join(_PROJECT_ROOT, "vendor", "ultralytics")
if _VENDOR not in sys.path:
    sys.path.insert(0, _VENDOR)

import yaml
import torch
from ultralytics import YOLO
from ultralytics.utils.loss import v8SegmentationLoss, SeesawBCE

ROOT = Path(_PROJECT_ROOT)
CONFIG_PATH = ROOT / "configs/train/stage2/seesaw_sweep_p08_q20.yaml"
DATASET_PATH = ROOT / "data/processed/yolo_seg_subset/data.yaml"
LOG_PATH = ROOT / "reports/phase2_smoke_test.log"
FALLBACK_WEIGHTS = ROOT / "runs/segment/seesaw_surgical_early/weights/best.pt"

SEESAW_LINE = re.compile(
    r"\[SEESAW\] iter=(?P<iter>\d+) \| cum_samples=(?P<cum_samples>\[[^\]]+\]) \| "
    r"mitigation: mean=(?P<mean>\S+) min=(?P<min>\S+) \| "
    r"compensation: active_frac=(?P<active_frac>\S+) max=(?P<max>\S+) \| "
    r"cls_loss_raw=(?P<cls_loss_raw>\S+) cls_loss_weighted=(?P<cls_loss_weighted>\S+)"
)


class Tee:
    def __init__(self, stream, fileobj):
        self.stream = stream
        self.fileobj = fileobj

    def write(self, data):
        self.stream.write(data)
        self.fileobj.write(data)

    def flush(self):
        self.stream.flush()
        self.fileobj.flush()


def main():
    with open(CONFIG_PATH) as f:
        cfg = yaml.safe_load(f)
    assert cfg.get("loss_type") == "seesaw", f"expected seesaw config, got {cfg.get('loss_type')}"
    seesaw_p = float(cfg["seesaw_p"])
    seesaw_q = float(cfg["seesaw_q"])
    print(f"[SMOKE] Loaded {CONFIG_PATH.name}: p={seesaw_p}, q={seesaw_q}")

    weights = cfg.get("model_preset", "")
    if not Path(weights).exists() and not (ROOT / weights).exists():
        print(f"[SMOKE] model_preset '{weights}' not found locally; using fallback {FALLBACK_WEIGHTS.relative_to(ROOT)}")
        weights = str(FALLBACK_WEIGHTS)

    orig_init = v8SegmentationLoss.__init__

    def patched_init(self, *args, **kwargs):
        orig_init(self, *args, **kwargs)
        self.bce = SeesawBCE(p=seesaw_p, q=seesaw_q)
        self.bce.seesaw_verbose = True
        print(f"[SMOKE] SeesawBCE injected with seesaw_verbose=True (p={seesaw_p}, q={seesaw_q})")

    v8SegmentationLoss.__init__ = patched_init

    if torch.cuda.is_available():
        device = 0
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    print(f"[SMOKE] device={device}, epochs=1, imgsz=1024, batch=8")

    model = YOLO(weights)

    # data.yaml uses `path: .`, which ultralytics resolves against the CWD
    os.chdir(DATASET_PATH.parent)

    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    log_file = open(LOG_PATH, "w")
    sys.stdout, sys.stderr = Tee(sys.__stdout__, log_file), Tee(sys.__stderr__, log_file)
    try:
        model.train(
            data=str(DATASET_PATH),
            epochs=1,
            imgsz=1024,
            batch=8,
            device=device,
            workers=4,
            freeze=23,
            val=False,
            amp=(device != "mps"),
            optimizer="AdamW",
            lr0=0.001,
            project=str(ROOT / "runs/smoke"),
            name="seesaw_smoke",
            exist_ok=True,
            plots=False,
        )
    finally:
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__
        log_file.close()

    log_text = LOG_PATH.read_text()
    records = [m.groupdict() for m in (SEESAW_LINE.search(l) for l in log_text.splitlines()) if m]
    print(f"[SMOKE] Parsed {len(records)} [SEESAW] lines from {LOG_PATH.relative_to(ROOT)}")

    # a) at least 5 [SEESAW] log lines
    assert len(records) >= 5, f"FAIL (a): only {len(records)} [SEESAW] lines logged"
    print(f"[SMOKE] (a) OK: {len(records)} >= 5 [SEESAW] lines")

    # b) cum_samples non-zero for all 7 classes
    cum = [float(x) for x in records[-1]["cum_samples"].strip("[]").split(",")]
    assert len(cum) == 7 and all(math.isfinite(c) and c > 0 for c in cum), f"FAIL (b): cum_samples={cum}"
    print(f"[SMOKE] (b) OK: cum_samples={cum}")

    # c) mitigation min < 1.0 (tail-class protection active)
    mit_min = min(float(r["min"]) for r in records)
    assert mit_min < 1.0, f"FAIL (c): mitigation min={mit_min}"
    print(f"[SMOKE] (c) OK: mitigation min={mit_min:.4f} < 1.0")

    # d) no NaN/Inf in logged loss values
    for r in records:
        for key in ("cls_loss_raw", "cls_loss_weighted", "mean", "min", "active_frac", "max"):
            v = float(r[key])
            assert math.isfinite(v), f"FAIL (d): {key}={r[key]} at iter={r['iter']}"
    print("[SMOKE] (d) OK: all logged values finite")

    # e) weighted loss differs from raw loss (weights actually applied)
    diffs = [abs(float(r["cls_loss_weighted"]) - float(r["cls_loss_raw"])) for r in records]
    assert max(diffs) > 1e-6, f"FAIL (e): max |weighted-raw|={max(diffs)}"
    print(f"[SMOKE] (e) OK: max |weighted-raw|={max(diffs):.6f}")

    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()
