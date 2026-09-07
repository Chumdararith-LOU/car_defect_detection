HEAD_LAYER = 23
NUM_LAYERS = 24

# YOLO26m-seg layer map: 0=Stem, 1-2=Stage1, 3-4=Stage2, 5-6=Stage3,
# 7-10=Stage4, 11-22=Neck, 23=Head.
# Each mode lists layer indices to UNFREEZE; everything else is frozen.
UNFREEZE_MODES = {
    "early_texture": {0, 1, 2, 3, 4, HEAD_LAYER},
    "et_stage3": set(range(7)) | {HEAD_LAYER},
    "et_backbone": set(range(11)) | {HEAD_LAYER},
    "et_neck_shallow": set(range(15)) | {HEAD_LAYER},
    "et_neck_deep": set(range(19)) | {HEAD_LAYER},
    "full_unfreeze": set(range(NUM_LAYERS)),
}


def apply_surgical_mode(model, mode):
    """Freeze/unfreeze model layers per UNFREEZE_MODES[mode]. Idempotent:
    every layer's requires_grad is set from the mode's set on each call."""
    layers = model.model.model
    if len(layers) != NUM_LAYERS:
        raise ValueError(f"mode '{mode}' expects {NUM_LAYERS} layers, model has {len(layers)}")
    unfreeze = UNFREEZE_MODES[mode]
    for i, layer in enumerate(layers):
        trainable = i in unfreeze
        for p in layer.parameters():
            p.requires_grad = trainable
    trainable_n = sum(p.numel() for p in model.model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.model.parameters())
    print(
        f"[🔪] mode={mode} unfreeze={sorted(unfreeze)} | "
        f"trainable params: {trainable_n:,} / {total:,} ({100 * trainable_n / total:.2f}%)"
    )
    return trainable_n


def self_check():
    # early_texture must match the legacy train.py block (layers 0-4 + head),
    # so sweep results are directly comparable to seesaw_sweep_control_bce (0.449).
    assert UNFREEZE_MODES["early_texture"] == {0, 1, 2, 3, 4, 23}, "early_texture drifted from seesaw control set"
    keys = list(UNFREEZE_MODES)
    for a, b in zip(keys, keys[1:]):
        assert UNFREEZE_MODES[a] < UNFREEZE_MODES[b], f"{a} must be a strict subset of {b}"
    assert all(HEAD_LAYER in s for s in UNFREEZE_MODES.values()), "head must be unfrozen in every mode"
    print("[surgical_modes] self-check OK")


if __name__ == "__main__":
    self_check()
