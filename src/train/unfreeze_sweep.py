import argparse
import csv
import os
import subprocess
import sys
import time
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
batch_size: {batch}
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


def write_configs(amp, batch):
    cfgs = {}
    for mode in UNFREEZE_MODES:
        p = CFG_DIR / f"unfreeze_{mode}.yaml"
        p.write_text(CFG_TEMPLATE.format(mode=mode, amp=str(amp).lower(), batch=batch))
        cfgs[mode] = p
    return cfgs


# ponytail: conservative floor, not a measured requirement — this workload (batch 8 @
# 1024px, yolo26m-seg) needs roughly 8-12GB; override with --min-free-gb on shared cards
MIN_FREE_GB = 10.0


def gpu_free_gb():
    if not torch.cuda.is_available():
        return None
    free, _ = torch.cuda.mem_get_info()
    return free / 1e9


def wait_for_gpu(min_free_gb=MIN_FREE_GB, timeout_s=1800, poll_s=60):
    free = gpu_free_gb()
    if free is None:
        return
    waited = 0
    while free is not None and free < min_free_gb:
        if waited >= timeout_s:
            sys.exit(
                f"ERROR: only {free:.1f}GB GPU free after waiting {timeout_s}s (need {min_free_gb}GB). "
                "Find the hog with nvidia-smi, kill it, lower --min-free-gb, then rerun with --modes <remaining>."
            )
        print(f"[gpu] {free:.1f}GB free < {min_free_gb}GB — waiting for VRAM (nvidia-smi shows who holds it)...")
        time.sleep(poll_s)
        waited += poll_s
        free = gpu_free_gb()


def quarantine_stale(mode):
    # move stale dirs aside so ultralytics doesn't auto-suffix new runs with "-2"
    for name in (mode, f"{mode}_eval"):
        d = RUN_ROOT / name
        if d.exists():
            dest = RUN_ROOT / "_partials" / f"{name}_{int(time.time())}"
            dest.parent.mkdir(parents=True, exist_ok=True)
            d.rename(dest)
            print(f"[quarantine] {d.relative_to(ROOT)} -> {dest.relative_to(ROOT)}")


def run_mode(mode, cfg, retries=1, min_free_gb=MIN_FREE_GB):
    env = {**os.environ, "PYTORCH_CUDA_ALLOC_CONF": "expandable_segments:True"}
    for attempt in range(retries + 1):
        wait_for_gpu(min_free_gb=min_free_gb)
        proc = subprocess.run(
            [sys.executable, "src/train/train.py", "--config", str(cfg.relative_to(ROOT))],
            cwd=ROOT, env=env,
        )
        if proc.returncode == 0 and (RUN_ROOT / mode / "results.csv").exists():
            return True
        print(f"FAILED: {mode} (attempt {attempt + 1}/{retries + 1})")
        if attempt < retries:
            quarantine_stale(mode)
    return False


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
    out = {
        "mode": mode,
        "mAP50": seg.map50,
        "mAP50-95": seg.map,
        **{c: per_cls.get(c, 0.0) for c in CLASS_COLS},
        "train_loss_final": train_final,
        "val_loss_final": val_final,
        "gap": train_final - val_final,
        "overfit": overfit,
    }
    # release parent-process VRAM (CUDA context + val cache) so the next training
    # subprocess gets the card back — holding it starved every run after the first collect()
    del r
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
    return out


def write_report(results, counts, batch):
    header = ["mode", "trainable_params", "mAP50", "mAP50-95", *CLASS_COLS,
              "train_loss_final", "val_loss_final", "overfit_gap(train-val)", "overfit_flag"]
    lines = [
        "# Backbone-unfreeze depth sweep (H1 capacity vs H2 surgical-specificity)",
        "",
        f"Fixed: bce loss, 20% subset, 25ep, imgsz 1024, batch {batch} (grad-accum to nbs=64; comparable across cells),",
        "AdamW lr0=0.001, patience 10,",
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
    parser.add_argument("--modes", nargs="+", choices=list(UNFREEZE_MODES),
                        help="run only these modes (e.g. after a crash, rerun the failed ones)")
    parser.add_argument("--min-free-gb", type=float, default=MIN_FREE_GB,
                        help=f"VRAM headroom required before each run (default {MIN_FREE_GB})")
    parser.add_argument("--batch", type=int, default=8,
                        help="batch size per run; use 4 if deep-unfreeze modes OOM (grad-accum keeps effective nbs=64)")
    args = parser.parse_args()

    self_check()
    print(f"early_texture unfreeze set == seesaw control set: {sorted(UNFREEZE_MODES['early_texture'])} (head={HEAD_LAYER})")

    if not CHECKPOINT.exists():
        sys.exit(f"ERROR: LP-FT warm-start checkpoint not found: {CHECKPOINT}\n"
                 f"Aborting — no fallback (a trained-model fallback biased the earlier smoke test).")
    print(f"Checkpoint: {CHECKPOINT}")

    amp = torch.cuda.is_available()  # true only on CUDA, matching control_bce; off on MPS/CPU
    cfgs = write_configs(amp, args.batch)
    if args.modes:
        cfgs = {m: c for m, c in cfgs.items() if m in args.modes}
    counts = param_counts()

    print(f"\n{len(cfgs)} runs (amp={amp}):")
    for mode, cfg in cfgs.items():
        print(f"  [{mode:>15}] trainable={counts[mode]:>12,}  python src/train/train.py --config {cfg.relative_to(ROOT)}")

    if args.dry_run:
        return

    results = []
    for mode in UNFREEZE_MODES:
        if mode in cfgs:
            print(f"\n=== STARTING: {mode} ===")
            quarantine_stale(mode)
            if not run_mode(mode, cfgs[mode], retries=1, min_free_gb=args.min_free_gb):
                print(f"FAILED: {mode}")
        # also collect modes outside --modes that already have results, so a
        # partial rerun doesn't clobber their rows in the report
        res = collect(mode) if (RUN_ROOT / mode / "results.csv").exists() else None
        results.append(res)

    write_report(results, counts, args.batch)


if __name__ == "__main__":
    main()
