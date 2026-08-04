import argparse
from pathlib import Path
import copy

import torch
from ultralytics import YOLO
from ultralytics.nn.tasks import SegmentationModel


def torch_load(path):
    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(path, map_location="cpu")


def main():
    parser = argparse.ArgumentParser(
        description="Remap Model 1 7-class head to Model 5 8-class head"
    )
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="Path to Model 1 checkpoint, e.g. epoch-101 best.pt",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output path for remapped 8-class init checkpoint",
    )
    parser.add_argument(
        "--nc",
        type=int,
        default=8,
        help="New number of classes",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print missing/unexpected keys but do not save",
    )
    args = parser.parse_args()

    print(f"[1/5] Loading source checkpoint: {args.source}")
    source = YOLO(args.source)
    source_model = source.model.float()
    src_state = source_model.state_dict()

    print("[2/5] Reading source model architecture config")
    model_cfg = getattr(source_model, "yaml", None)

    if model_cfg is None:
        raise RuntimeError(
            "Could not read model YAML from source checkpoint. "
            "We need the source model architecture config to rebuild an 8-class model."
        )

    model_cfg = copy.deepcopy(model_cfg)

    if not isinstance(model_cfg, dict):
        model_cfg = dict(model_cfg)

    # Remove old class names so old 7-class names do not conflict with nc=8.
    model_cfg.pop("names", None)

    old_nc = model_cfg.get("nc", None)
    model_cfg["nc"] = args.nc

    print(f"[3/5] Building target model: old nc={old_nc}, new nc={args.nc}")
    target = SegmentationModel(model_cfg, ch=3, nc=args.nc)

    print("[4/5] Filtering source weights before strict=False load")

    target_state = target.state_dict()
    filtered_src_state = {}
    skipped_shape_mismatch = []
    skipped_not_in_target = []

    for key, value in src_state.items():
        if key not in target_state:
            skipped_not_in_target.append(key)
        elif target_state[key].shape != value.shape:
            skipped_shape_mismatch.append(
                (key, tuple(value.shape), tuple(target_state[key].shape))
            )
        else:
            filtered_src_state[key] = value

    missing, unexpected = target.load_state_dict(filtered_src_state, strict=False)

    print("\nSkipped source keys due to shape mismatch, expected old 7-class head:")
    for key, src_shape, tgt_shape in skipped_shape_mismatch:
        print(f"  shape_mismatch: {key} | source={src_shape} | target={tgt_shape}")

    print("\nSkipped source keys not present in target model:")
    for key in skipped_not_in_target:
        print(f"  not_in_target: {key}")

    print("\nMissing keys, should mostly be new 8-class head layers:")
    for k in missing:
        print(f"  missing: {k}")

    print("\nUnexpected keys, should mostly be old 7-class head layers:")
    for k in unexpected:
        print(f"  unexpected: {k}")

    if len(missing) == 0:
        print(
            "[WARNING] No missing keys found. This is suspicious because nc changed from 7 to 8."
        )

    if args.dry_run:
        print("\n[DRY RUN] Not saving checkpoint.")
        return

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[5/5] Saving remapped checkpoint to: {out_path}")

    raw_ckpt = torch_load(args.source)
    payload = {}

    if isinstance(raw_ckpt, dict):
        payload.update(raw_ckpt)

    # Remove training-state objects that are not needed for the remapped init checkpoint.
    payload.pop("optimizer", None)
    payload.pop("ema", None)
    payload.pop("best_fitness", None)

    payload["model"] = target
    payload["nc"] = args.nc
    payload["epoch"] = 0

    torch.save(payload, out_path)

    print("Verifying saved checkpoint can be loaded by YOLO...")
    check = YOLO(str(out_path))
    print(
        f"Verification OK. Loaded checkpoint nc={getattr(check.model, 'nc', 'unknown')}"
    )


if __name__ == "__main__":
    main()
