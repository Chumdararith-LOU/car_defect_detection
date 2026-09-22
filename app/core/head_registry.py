"""Register the custom objectness head so pickled checkpoints can be unpickled.

The objectness-branch model was trained with a custom segmentation head
``Segment26WithObjectness``. When Ultralytics saves the checkpoint, the head
class is pickled by reference (module path + class name). At load time Python
must be able to import that module path and find the class.

This module makes the class importable under every plausible historical path so
``torch.load`` succeeds regardless of which path the checkpoint was pickled
with. Import this module (or call :func:`register_custom_head`) BEFORE loading
any objectness checkpoint.
"""
import sys
import types
import logging

logger = logging.getLogger("head_registry")

_REGISTERED = False


def register_custom_head() -> None:
    """Register ``Segment26WithObjectness`` under all plausible module paths."""
    global _REGISTERED
    if _REGISTERED:
        return

    from app.core.custom_head import Segment26WithObjectness

    # 1) Attach to the ultralytics head module (where the class logically lives).
    try:
        import ultralytics.nn.modules.head as head_module
        head_module.Segment26WithObjectness = Segment26WithObjectness
    except Exception:  # pragma: no cover
        logger.exception("Could not attach head to ultralytics.nn.modules.head")

    # 2) Register synthetic modules for every historical pickle path so that
    #    torch.load can resolve whichever reference the checkpoint stores.
    historical_paths = [
        "src.stage2.models.segment_head_with_obj",
        "src.models.segment_head_with_obj",
        "segment_head_with_obj",
        "src.stage2.models",
        "src.models",
    ]
    for path in historical_paths:
        if path in sys.modules:
            mod = sys.modules[path]
        else:
            mod = types.ModuleType(path)
            sys.modules[path] = mod
        setattr(mod, "Segment26WithObjectness", Segment26WithObjectness)

    # Ensure the class's own __module__ also resolves.
    own_module = Segment26WithObjectness.__module__
    if own_module not in sys.modules:
        mod = types.ModuleType(own_module)
        sys.modules[own_module] = mod
    setattr(sys.modules[own_module], "Segment26WithObjectness", Segment26WithObjectness)

    _REGISTERED = True
    logger.info(
        "Segment26WithObjectness registered under %d module paths",
        len(historical_paths) + 2,
    )


# Register on import so callers only need ``import app.core.head_registry``.
register_custom_head()
