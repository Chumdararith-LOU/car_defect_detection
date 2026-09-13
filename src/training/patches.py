"""Monkey-patch utilities for YOLO models."""
from ultralytics.nn.tasks import SegmentationModel
from ultralytics.nn.modules.head import Segment


def patch_yolo_class(model, new_head_class):
    """Replace the model's head with a custom one."""    
    # Get current head
    old_head = model.model[-1]
    
    # Replace head with custom head class
    if isinstance(old_head, (Segment)):
        # Recreate module
        new_head_instance = new_head_class(
            nc=old_head.nc,
            nm=old_head.nm,
            npr=old_head.npr,
            reg_max=old_head.reg_max,
            ch=old_head.ch,
            end2end=getattr(old_head, 'end2end', False)
        )
        # Replace head in model
        model.model[-1] = new_head_instance
    else:
        raise ValueError("Expected instance of Segment or similar to be at model[-1]")
