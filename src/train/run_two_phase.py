#!/usr/bin/env python3
"""Two-phase LP-FT pipeline driver for configs/train/stage2/clean_retrain_augmented.yaml.

  --validate  check config + prerequisites, print CONFIG VALIDATED
  --run       data prep -> phase 1 -> phase 2 -> eval
"""

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

SEVEN_CLASSES = ["broken_lamp", "corrosion", "crack", "dent", "disjoint_part", "glass_shatter", "scratch"]
IMG_EXTS = (".jpg", ".jpeg", ".png", ".bmp", ".webp")


def load_cfg(path: Path) -> dict:
    with open(path) as f:
        cfg = yaml.safe_load(f)
    for section in ("common", "phase1", "phase2", "eval", "clean_negatives"):
        if section not in cfg:
            raise ValueError(f"config missing section: {section}")
    return cfg


def check_dataset(data_yaml: Path, errors: list) -> None:
    if not data_yaml.exists():
        errors.append(f"dataset yaml missing: {data_yaml}")
        return
    ds = yaml.safe_load(data_yaml.read_text())
    names = ds.get("names", {})
    if [names.get(i) for i in range(7)] != SEVEN_CLASSES:
        errors.append(f"dataset names != 7-class taxonomy: {names}")
    base = data_yaml.parent
    for split in ("train", "val", "test"):
        if split not in ds:
            errors.append(f"dataset yaml missing split: {split}")
            continue
        img_dir = base / ds[split]
        lbl_dir = img_dir.parent.parent / "labels" / img_dir.name
        if not img_dir.is_dir():
            errors.append(f"{split}: image dir missing: {img_dir}")
            continue
        imgs = {p.stem for p in img_dir.iterdir() if p.suffix.lower() in IMG_EXTS}
        lbls = {p.stem for p in lbl_dir.glob("*.txt")} if lbl_dir.is_dir() else set()
        if imgs - lbls:
            errors.append(f"{split}: {len(imgs - lbls)} images without labels (e.g. {sorted(imgs - lbls)[:3]})")
        if lbls - imgs:
            errors.append(f"{split}: {len(lbls - imgs)} labels without images")
        bad = []
        for p in sorted(lbl_dir.glob("*.txt")):
            for line in p.read_text().splitlines():
                parts = line.split()
                if parts and not (parts[0].isdigit() and 0 <= int(parts[0]) < 7):
                    bad.append(str(p.relative_to(REPO_ROOT)))
                    break
        if bad:
            errors.append(f"{split}: bad class ids in {bad[:3]}")
        print(f"  {split}: {len(imgs)} images, {len(lbls)} labels")


def validate(cfg: dict) -> None:
    errors = []

    print("[validate] 1. config sections + YAML parse: OK")

    print("[validate] 2. phase 1 checkpoint")
    p1 = REPO_ROOT / cfg["phase1"]["model_preset"]
    if not p1.exists():
        errors.append(f"phase1 checkpoint missing: {cfg['phase1']['model_preset']}")
    else:
        print(f"  {p1.relative_to(REPO_ROOT)} ({p1.stat().st_size / 1e6:.0f} MB)")

    print("[validate] 3. augmented dataset")
    check_dataset(REPO_ROOT / cfg["common"]["dataset_config"], errors)

    print("[validate] 4. clean negatives")
    cn = cfg["clean_negatives"]
    src = REPO_ROOT / cn["source"]
    imgs = [p for p in src.iterdir() if p.suffix.lower() in IMG_EXTS] if src.is_dir() else []
    if not imgs:
        errors.append(f"clean source empty or missing: {cn['source']}")
    lbl_dir = src.parent.parent / "labels" / src.name
    nonempty = [p for p in lbl_dir.glob("*.txt") if p.stat().st_size > 0] if lbl_dir.is_dir() else []
    if nonempty:
        errors.append(f"{len(nonempty)} clean images have non-empty label files")
    print(f"  {len(imgs)} clean images, {len(nonempty)} with non-empty labels (must be 0)")

    if errors:
        print("\n[validate] FAILED:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("\nCONFIG VALIDATED")


def build_car_only_test(cfg: dict) -> None:
    ev = cfg["eval"]
    out_dir = REPO_ROOT / ev["car_only_test_dir"]
    img_out, lbl_out = out_dir / "images", out_dir / "labels"
    img_out.mkdir(parents=True, exist_ok=True)
    lbl_out.mkdir(parents=True, exist_ok=True)
    names = [l.strip() for l in (REPO_ROOT / ev["car_only_test_list"]).read_text().splitlines() if l.strip()]
    src_img = REPO_ROOT / "data/processed/yolo_seg/images/test"
    src_lbl = REPO_ROOT / "data/processed/yolo_seg/labels/test"
    n = 0
    for name in names:
        src = src_img / name
        if not src.exists():
            print(f"  [warn] missing source image: {name}")
            continue
        dst = img_out / name
        if not dst.exists():
            os.symlink(os.path.relpath(src, img_out), dst)
        stem = Path(name).stem
        lbl_src, lbl_dst = src_lbl / f"{stem}.txt", lbl_out / f"{stem}.txt"
        if not lbl_dst.exists():
            if lbl_src.exists():
                shutil.copy2(lbl_src, lbl_dst)
            else:
                lbl_dst.touch()
        n += 1
    (out_dir / "data.yaml").write_text(
        f"path: {out_dir.resolve()}\nval: images\nnames:\n"
        + "".join(f"  {i}: {c}\n" for i, c in enumerate(SEVEN_CLASSES))
    )
    print(f"[data] car-only test set: {n}/{len(names)} images -> {ev['car_only_test_dir']}")


def inject_clean_negatives(cfg: dict) -> None:
    cn = cfg["clean_negatives"]
    cmd = [
        sys.executable, str(REPO_ROOT / cn["script"]),
        "--neg-ratio", str(cn["ratio"]),
        "--seed", str(cn["seed"]),
        "--target", "yolo_seg_clean_augmented",
    ]
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)


def run_phase(cfg: dict, phase: str) -> Path:
    flat = {**cfg["common"], **cfg[phase]}
    fd, tmp = tempfile.mkstemp(suffix=".yaml", prefix=f"two_phase_{phase}_")
    with os.fdopen(fd, "w") as f:
        yaml.safe_dump(flat, f)
    # dataset data.yaml uses 'path: .' which ultralytics resolves against CWD,
    # not the yaml's directory — pass a temp copy with an absolute path
    ds_src = REPO_ROOT / flat["dataset_config"]
    ds = yaml.safe_load(ds_src.read_text())
    ds["path"] = str(ds_src.parent.resolve())
    fd2, tmp_data = tempfile.mkstemp(suffix=".yaml", prefix=f"two_phase_{phase}_data_")
    with os.fdopen(fd2, "w") as f:
        yaml.safe_dump(ds, f)
    try:
        subprocess.run(
            [sys.executable, "src/train/train.py", "--config", tmp, "--data", tmp_data],
            check=True, cwd=REPO_ROOT,
        )
    finally:
        os.unlink(tmp)
        os.unlink(tmp_data)
    # ultralytics appends -2, -3 ... on run-name collision; take the newest best.pt
    candidates = sorted(
        (REPO_ROOT / "runs/segment" / flat["project_name"]).glob(f"{flat['run_name']}*/weights/best.pt"),
        key=lambda p: p.stat().st_mtime,
    )
    if not candidates:
        raise RuntimeError(f"{phase}: no best.pt under runs/segment/{flat['project_name']}/{flat['run_name']}*")
    best = candidates[-1]
    print(f"[{phase}] best.pt: {best.relative_to(REPO_ROOT)}")
    return best


def run(cfg: dict) -> None:
    validate(cfg)
    build_car_only_test(cfg)
    inject_clean_negatives(cfg)

    p1_best = run_phase(cfg, "phase1")
    p1_final = p1_best.parent / "phase1_best.pt"
    shutil.copy2(p1_best, p1_final)
    print(f"[phase1] checkpoint saved as {p1_final.relative_to(REPO_ROOT)}")

    cfg2 = {**cfg, "phase2": {**cfg["phase2"], "model_preset": str(p1_final.relative_to(REPO_ROOT))}}
    p2_best = run_phase(cfg2, "phase2")

    ev = cfg["eval"]
    cmd = [
        sys.executable, "src/eval/eval_car_only.py",
        "--weights", str(p2_best.relative_to(REPO_ROOT)),
        "--car-test-data", str((REPO_ROOT / ev["car_only_test_dir"] / "data.yaml").relative_to(REPO_ROOT)),
        "--clean-dir", ev["clean_eval_dir"],
        "--noncar-list", ev["noncar_test_list"],
        "--imgsz", str(cfg["common"]["imgsz"]),
        "--fpr-thresholds", ",".join(str(t) for t in ev["fpr_thresholds"]),
        "--baseline", f"{ev['baseline']['run']} = {ev['baseline']['mask_map50']}",
        "--out", "reports/clean_retrain_augmented_eval.md",
    ]
    subprocess.run(cmd, check=True, cwd=REPO_ROOT)
    print("[done] two-phase LP-FT complete; report: reports/clean_retrain_augmented_eval.md")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", required=True)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--validate", action="store_true")
    g.add_argument("--run", action="store_true")
    args = ap.parse_args()

    cfg = load_cfg(Path(args.config))
    if args.validate:
        validate(cfg)
    else:
        run(cfg)


if __name__ == "__main__":
    main()
