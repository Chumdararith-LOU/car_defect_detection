import argparse
import csv
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "vendor" / "ultralytics"))

import torch
from ultralytics import YOLO

from surgical_modes import UNFREEZE_MODES, HEAD_LAYER, apply_surgical_mode, self_check

CFG_DIR = ROOT / "configs" / "train" / "stage2"
# Same LP-FT warm-start preset the seesaw control_bce run used — no fallbacks.
CHECKPOINT = ROOT / "model5_resume_adapt" / "model1_remapped_7class_init.pt"
DATASET = ROOT / "data" / "processed" / "yolo_seg_subset" / "data.yaml"
RUN_ROOT = ROOT / "runs" / "segment" / "unfreeze_sweep"  # ultralytics saves runs/segment/<project>/<name>
REPORT = ROOT / "reports" / "unfreeze_sweep_results.md"
CLASS_COLS = ["corrosion", "disjoint_part", "glass_shatter", "broken_lamp", "scratch", "crack", "dent"]

CFG_TEMPLATE = """task: segment
loss_type: bce
model_preset: model5_resume_adapt/model1_remapped_7class_init.pt

# train.py freezes every layer outside surgical_modes.UNFREEZE_MODES[{mode}]
surgical_mode: {mode}

project_name: unfreeze_sweep
run_name: {mode}
multi_scale: false

# 20% stratified subset, same as seesaw sweep (control_bce = 0.449 Mask mAP50)
dataset_config: "data/processed/yolo_seg_subset/data.yaml"
epochs: 25
imgsz: 1024
batch_size: 8
patience: 10
device: 0
workers: 8
amp: {amp}

freeze: 23
optimizer: AdamW
lr0: 0.001
lrf: 0.01

augmentations:
  hsv_h: 0.03
  hsv_s: 0.4
  hsv_v: 0.5
  degrees: 15.0
  scale: 0.2
  perspective: 0.0005
  fliplr: 0.5
  mosaic: 0.0
  mixup: 0.0
  erasing: 0.2
  close_mosaic: 10
"""


def param_counts():
    model = YOLO(str(CHECKPOINT))
    return {mode: apply_surgical_mode(model, mode) for mode in UNFREEZE_MODES}


def write_configs(amp):
    cfgs = {}
    for mode in UNFREEZE_MODES:
        p = CFG_DIR / f"unfreeze_{mode}.yaml"
        p.write_text(CFG_TEMPLATE.format(mode=mode, amp=str(amp).lower()))
        cfgs[mode] = p
    return cfgs


def loss_sums(row, prefix):
    return sum(float(v) for k, v in row.items() if k.strip().startswith(prefix))


def collect(mode):
    run_dir = RUN_ROOT / mode
    csv_path = run_dir / "results.csv"
    if not csv_path.exists():
        return None
    rows = list(csv.DictReader(open(csv_path)))
    if not rows:
        return None
    train_final = loss_sums(rows[-1], "train/")
    val_final = loss_sums(rows[-1], "val/")
    val_min = min(loss_sums(r, "val/") for r in rows)
    # ponytail: overfit flag = val loss ended >10% above its own min; per-epoch curve check if this misfires
    overfit = val_final > val_min * 1.10

    best = run_dir / "weights" / "best.pt"
    device = 0 if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    r = YOLO(str(best)).val(
        data=str(DATASET), imgsz=1024, batch=8, device=device,
        project=str(RUN_ROOT), name=f"{mode}_eval", exist_ok=True, plots=False,
    )
    seg = r.seg
    per_cls = {r.names[int(c)]: seg.ap50[i] for i, c in enumerate(seg.ap_class_index)}
    return {
        "mode": mode,
        "mAP50": seg.map50,
        "mAP50-95": seg.map,
        **{c: per_cls.get(c, 0.0) for c in CLASS_COLS},
        "train_loss_final": train_final,
        "val_loss_final": val_final,
        "gap": train_final - val_final,
        "overfit": overfit,
    }


def write_report(results, counts):
    header = ["mode", "trainable_params", "mAP50", "mAP50-95", *CLASS_COLS,
              "train_loss_final", "val_loss_final", "overfit_gap(train-val)", "overfit_flag"]
    lines = [
        "# Backbone-unfreeze depth sweep (H1 capacity vs H2 surgical-specificity)",
        "",
        "Fixed: bce loss, 20% subset, 25ep, imgsz 1024, batch 8, AdamW lr0=0.001, patience 10,",
        f"warm-start `{CHECKPOINT.relative_to(ROOT)}`. Per-class columns = Mask mAP50.",
        "Baseline to beat: seesaw_sweep_control_bce = 0.449 Mask mAP50 (early_texture, patience 15, amp true).",
        "",
        "| " + " | ".join(header) + " |",
        "|" + "---|" * len(header),
    ]
    for res in results:
        if res is None:
            continue
        m = res["mode"]
        lines.append(
            f"| {m} | {counts.get(m, 0):,} | {res['mAP50']:.4f} | {res['mAP50-95']:.4f} | "
            + " | ".join(f"{res[c]:.4f}" for c in CLASS_COLS)
            + f" | {res['train_loss_final']:.4f} | {res['val_loss_final']:.4f} | {res['gap']:.4f} | "
            + ("⚠ OVERFIT" if res["overfit"] else "ok") + " |"
        )
    for m in UNFREEZE_MODES:
        if not any(res and res["mode"] == m for res in results):
            lines.append(f"| {m} | {counts.get(m, 0):,} | FAILED | | | | | | | | | | |")
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n")
    print(f"Wrote {REPORT.relative_to(ROOT)}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="print commands + param counts, don't train")
    args = parser.parse_args()

    self_check()
    print(f"early_texture unfreeze set == seesaw control set: {sorted(UNFREEZE_MODES['early_texture'])} (head={HEAD_LAYER})")

    if not CHECKPOINT.exists():
        sys.exit(f"ERROR: LP-FT warm-start checkpoint not found: {CHECKPOINT}\n"
                 f"Aborting — no fallback (a trained-model fallback biased the earlier smoke test).")
    print(f"Checkpoint: {CHECKPOINT}")

    amp = torch.cuda.is_available()  # true only on CUDA, matching control_bce; off on MPS/CPU
    cfgs = write_configs(amp)
    counts = param_counts()

    print(f"\n{len(cfgs)} runs (amp={amp}):")
    for mode, cfg in cfgs.items():
        print(f"  [{mode:>15}] trainable={counts[mode]:>12,}  python src/train/train.py --config {cfg.relative_to(ROOT)}")

    if args.dry_run:
        return

    results = []
    for mode, cfg in cfgs.items():
        print(f"\n=== STARTING: {mode} ===")
        proc = subprocess.run(
            [sys.executable, "src/train/train.py", "--config", str(cfg.relative_to(ROOT))],
            cwd=ROOT,
        )
        if proc.returncode != 0:
            print(f"FAILED: {mode}")
        res = collect(mode) if (RUN_ROOT / mode / "results.csv").exists() else None
        results.append(res)

    write_report(results, counts)


if __name__ == "__main__":
    main()
