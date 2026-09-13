"""Surgical fine-tuning callback for YOLO models."""
from ultralytics import YOLO
from torch.nn import Module
from src.train.surgical_modes import apply_surgical_mode


class SurgicalFineTuneCallback:
    """Callback to perform surgical fine-tuning before training starts.
    
    This callback MUST run BEFORE the optimizer is constructed. It unfreezes
    model layers and rebuilds the optimizer to include newly-unfrozen parameters.
    """
    
    def __init__(self, mode="full_unfreeze"):
        self.name = "SurgicalFineTune"
        self.mode = mode
        
    def __call__(self, trainer):
        """Perform surgical fine-tuning BEFORE optimizer construction.
        
        The callback order is:
        1. on_pretrain_routine_start: apply surgical mode (unfreeze layers)
        2. _setup_train: builds optimizer (now includes unfrozen params)
        
        We use on_pretrain_routine_start to ensure unfreeze happens first.
        """
        print(f"[SurgicalFineTune] Applying mode '{self.mode}'...")
        apply_surgical_mode(trainer.model, self.mode)
        
        print("[SurgicalFineTune] Rebuilding optimizer to include newly-unfrozen parameters...")
        trainer.optimizer = trainer.build_optimizer(
            model=trainer.model,
            name=trainer.args.optimizer,
            lr=trainer.args.lr0,
            momentum=trainer.args.momentum,
            decay=trainer.args.weight_decay * trainer.batch_size * trainer.accumulate / trainer.args.nbs,
            iterations=trainer.epochs * len(trainer.train_loader),
        )
        trainer._setup_scheduler()
        print("[SurgicalFineTune] Optimizer rebuilt successfully.")


class LPFTCallback:
    """Loss-based Progressive Fine-Tuning callback."""
    
    def __init__(self):
        self.name = "LPFT"
        
    def __call__(self, trainer):
        """Perform loss-based progressive fine-tuning."""
        print("Performing LPFT...")
        # Add your LPFT logic here if needed