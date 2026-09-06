"""Utility to load a YOLO checkpoint and restore the objectness head."""
import torch
from ultralytics import YOLO
from src.models.segment_head_with_obj import Segment26WithObjectness
import ultralytics.nn.modules.head as head_module

# Register the custom head class so torch.load / YOLO can find it
head_module.Segment26WithObjectness = Segment26WithObjectness


def load_yolo_with_objectness(weights_path: str) -> YOLO:
    """Load a YOLO model and ensure the objectness head is present."""
    model = YOLO(weights_path)
    head = model.model.model[-1]

    if hasattr(head, 'cv_obj'):
        print(f"✅ cv_obj already present ({type(head).__name__})")
        return model

    # Head was lost during save/load — rebuild it
    print(f"⚠️  Head is {type(head).__name__}, rebuilding with cv_obj...")
    ch = tuple(
        (head.cv2[i][0].conv.in_channels if hasattr(head.cv2[i][0], 'conv')
         else head.cv2[i][0].in_channels)
        for i in range(head.nl)
    )
    new_head = Segment26WithObjectness(
        nc=head.nc, nm=head.nm, npr=head.npr,
        reg_max=head.reg_max,
        end2end=getattr(head, 'end2end', False),
        ch=ch,
    )

    # Copy existing head weights
    old_sd = head.state_dict()
    new_sd = new_head.state_dict()
    for k, v in old_sd.items():
        if k in new_sd and new_sd[k].shape == v.shape:
            new_sd[k] = v

    # Try to recover cv_obj weights from the raw checkpoint
    try:
        raw = torch.load(weights_path, map_location='cpu')
        raw_sd = raw['model'].state_dict() if hasattr(raw.get('model'), 'state_dict') else {}
        prefix = f"model.{len(model.model.model) - 1}."
        recovered = 0
        for k, v in raw_sd.items():
            if k.startswith(prefix) and 'cv_obj' in k:
                local_key = k[len(prefix):]
                if local_key in new_sd and new_sd[local_key].shape == v.shape:
                    new_sd[local_key] = v
                    recovered += 1
        if recovered > 0:
            print(f"  Recovered {recovered} cv_obj tensors from checkpoint")
        else:
            print("  ⚠️  No cv_obj weights found in checkpoint — using init values")
    except Exception as e:
        print(f"  ⚠️  Could not read raw checkpoint: {e}")

    new_head.load_state_dict(new_sd)
    new_head.stride = head.stride
    model.model.model[-1] = new_head
    print("✅ Head rebuilt with cv_obj")
    return model