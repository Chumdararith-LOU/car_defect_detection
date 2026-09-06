"""
Model 1 -> Model 5 7-class head remap.

Old Model 1 classes:
    0 dent
    1 scratch
    2 crack
    3 glass_shatter
    4 broken_component
    5 missing_component
    6 corrosion

New official 7-class schema:
    0 dent
    1 scratch
    2 crack
    3 glass_shatter
    4 broken_lamp
    5 corrosion
    6 disjoint_part

Mapping:
    old 0 -> new 0   dent
    old 1 -> new 1   scratch
    old 2 -> new 2   crack
    old 3 -> new 3   glass_shatter
    old 4 -> new 4   broken_component -> broken_lamp
    old 5 -> discarded, missing_component was annotated on nothing
    old 6 -> new 5   corrosion
    new 6 -> fresh random init, disjoint_part is a new class
"""

import argparse
import copy
from pathlib import Path

import torch
from ultralytics import YOLO
from ultralytics.nn.tasks import SegmentationModel

OLD_NAMES = {
    0: "dent",
    1: "scratch",
    2: "crack",
    3: "glass_shatter",
    4: "broken_component",
    5: "missing_component",
    6: "corrosion",
}

NEW_NAMES = {
    0: "dent",
    1: "scratch",
    2: "crack",
    3: "glass_shatter",
    4: "broken_lamp",
    5: "corrosion",
    6: "disjoint_part",
}

OLD_TO_NEW = {
    0: 0,
    1: 1,
    2: 2,
    3: 3,
    4: 4,
    6: 5,
}

DISCARDED_OLD_IDS = [5]
FRESH_NEW_IDS = [6]

CLASS_KEY_SUBSTRINGS = (
    "cv3.0.2",
    "cv3.1.2",
    "cv3.2.2",
    "one2one_cv3.0.2",
    "one2one_cv3.1.2",
    "one2one_cv3.2.2",
    "proto.semseg.2",
)


def torch_load(path):
    try:
        return torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        return torch.load(path, map_location="cpu")


def is_class_key(key):
    if not key.startswith("model.23."):
        return False

    if not key.endswith((".weight", ".bias")):
        return False

    return any(sub in key for sub in CLASS_KEY_SUBSTRINGS)


def main():
    parser = argparse.ArgumentParser(
        description="Remap Model 1 7-class head to new official 7-class head."
    )
    parser.add_argument(
        "--source",
        type=str,
        required=True,
        help="Path to Model 1 checkpoint best.pt",
    )
    parser.add_argument(
        "--out",
        type=str,
        required=True,
        help="Output path for remapped 7-class init checkpoint",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print and verify surgery plan but do not save",
    )
    args = parser.parse_args()

    print(f"[1/7] Loading source checkpoint: {args.source}")
    source = YOLO(args.source)
    source_model = source.model.float()
    src_state = source_model.state_dict()

    print("[2/7] Reading source model architecture config")
    model_cfg = getattr(source_model, "yaml", None)
    if model_cfg is None:
        raise RuntimeError(
            "Could not read model YAML from source checkpoint. "
            "We need the source architecture config to rebuild the target model."
        )

    model_cfg = copy.deepcopy(model_cfg)
    if not isinstance(model_cfg, dict):
        model_cfg = dict(model_cfg)

    old_nc = model_cfg.get("nc", None)
    new_nc = 7

    print(f"      old nc: {old_nc}")
    print(f"      new nc: {new_nc}")
    print(f"      old names: {getattr(source_model, 'names', OLD_NAMES)}")
    print(f"      new names: {NEW_NAMES}")

    model_cfg["nc"] = new_nc
    model_cfg["names"] = NEW_NAMES

    print("[3/7] Building target model with new official 7-class names")
    target = SegmentationModel(model_cfg, ch=3, nc=new_nc)

    if hasattr(target, "names"):
        target.names = NEW_NAMES

    if hasattr(target, "yaml") and isinstance(target.yaml, dict):
        target.yaml["names"] = NEW_NAMES
        target.yaml["nc"] = new_nc

    target_state = target.state_dict()
    new_state = {k: v.clone() for k, v in target_state.items()}

    print("[4/7] Copying weights with partial head remap")

    class_keys = []
    direct_copy_keys = []
    skipped_shape_mismatch = []
    target_keys_not_in_source = []

    for key, target_tensor in target_state.items():
        if key not in src_state:
            target_keys_not_in_source.append(key)
            continue

        src_tensor = src_state[key]

        if is_class_key(key):
            class_keys.append(key)

            if src_tensor.shape != target_tensor.shape:
                skipped_shape_mismatch.append(
                    (key, tuple(src_tensor.shape), tuple(target_tensor.shape))
                )
                continue

            # new_state already contains fresh random init for all new classes.
            # Copy only the valid old class rows into their new positions.
            for old_idx, new_idx in OLD_TO_NEW.items():
                new_state[key][new_idx] = src_tensor[old_idx]

        else:
            if src_tensor.shape == target_tensor.shape:
                new_state[key] = src_tensor
                direct_copy_keys.append(key)
            else:
                skipped_shape_mismatch.append(
                    (key, tuple(src_tensor.shape), tuple(target_tensor.shape))
                )

    src_keys_not_in_target = [k for k in src_state.keys() if k not in target_state]

    print(f"      direct copied tensors: {len(direct_copy_keys)}")
    print(f"      remapped class tensors: {len(class_keys)}")
    print(f"      target keys not in source: {len(target_keys_not_in_source)}")
    print(f"      source keys not in target: {len(src_keys_not_in_target)}")
    print(f"      shape mismatches: {len(skipped_shape_mismatch)}")

    if len(class_keys) != 14:
        print(
            f"[WARNING] Expected 14 class tensors, found {len(class_keys)}. "
            "Please inspect before continuing."
        )

    if target_keys_not_in_source:
        print("\nTarget keys not found in source:")
        for k in target_keys_not_in_source[:50]:
            print(f"  {k}")

    if src_keys_not_in_target:
        print("\nSource keys not found in target:")
        for k in src_keys_not_in_target[:50]:
            print(f"  {k}")

    if skipped_shape_mismatch:
        print("\nShape mismatches:")
        for k, src_shape, tgt_shape in skipped_shape_mismatch:
            print(f"  {k}: source={src_shape}, target={tgt_shape}")

    print("\nClass tensors being remapped:")
    for k in class_keys:
        print(f"  {k}")

    print("\nMapping plan:")
    for old_idx, new_idx in OLD_TO_NEW.items():
        print(
            f"  old {old_idx} {OLD_NAMES[old_idx]} -> new {new_idx} {NEW_NAMES[new_idx]}"
        )

    for old_idx in DISCARDED_OLD_IDS:
        print(f"  old {old_idx} {OLD_NAMES[old_idx]} -> DISCARDED")

    for new_idx in FRESH_NEW_IDS:
        print(f"  new {new_idx} {NEW_NAMES[new_idx]} -> FRESH RANDOM INIT")

    print("\n[5/7] Loading new state dict into target model")
    missing, unexpected = target.load_state_dict(new_state, strict=False)

    if missing or unexpected:
        print("Missing keys:")
        for k in missing:
            print(f"  {k}")
        print("Unexpected keys:")
        for k in unexpected:
            print(f"  {k}")
        raise RuntimeError(
            "State dict load was not clean. Do not save this checkpoint."
        )

    print("      clean load: no missing or unexpected keys")

    print("[6/7] Verifying remapped class tensors")
    loaded_state = target.state_dict()
    all_mapped_ok = True

    for key in class_keys:
        src_tensor = src_state[key]
        tgt_tensor = loaded_state[key]

        for old_idx, new_idx in OLD_TO_NEW.items():
            if not torch.allclose(tgt_tensor[new_idx], src_tensor[old_idx]):
                all_mapped_ok = False
                print(f"      MISMATCH: {key} old={old_idx} new={new_idx}")

    print(f"      mapped class tensor check: {'OK' if all_mapped_ok else 'FAILED'}")

    for key in class_keys:
        tensor = loaded_state[key]
        if key.endswith(".weight"):
            print(
                f"      {key}: new disjoint_part row norm = {float(tensor[6].norm()):.6f}"
            )
        else:
            print(
                f"      {key}: new disjoint_part bias mean = {float(tensor[6].mean()):.6f}"
            )

    if not all_mapped_ok:
        raise RuntimeError("Mapped class tensor verification failed.")

    if args.dry_run:
        print("\n[DRY RUN] Not saving checkpoint.")
        return

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"[7/7] Saving remapped checkpoint to: {out_path}")

    raw_ckpt = torch_load(args.source)
    payload = {}

    if isinstance(raw_ckpt, dict):
        payload.update(raw_ckpt)

    payload.pop("optimizer", None)
    payload.pop("ema", None)
    payload.pop("best_fitness", None)

    payload["model"] = target
    payload["nc"] = new_nc
    payload["names"] = NEW_NAMES
    payload["epoch"] = 0

    torch.save(payload, out_path)

    print("Verifying saved checkpoint can be loaded by YOLO...")
    check = YOLO(str(out_path))

    print("Verification OK.")
    print(f"  nc: {getattr(check.model, 'nc', 'unknown')}")
    print(f"  names: {getattr(check.model, 'names', 'unknown')}")


if __name__ == "__main__":
    main()
