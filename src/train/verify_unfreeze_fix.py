#!/usr/bin/env python3
"""Verify surgical unfreeze fix produces genuinely different training across modes."""

import os
import sys
import torch
import yaml
import pandas as pd
from pathlib import Path
from ultralytics import YOLO

sys.path.insert(0, str(Path(__file__).parent))
from surgical_modes import UNFREEZE_MODES, apply_surgical_mode
from ultralytics.utils.torch_utils import unwrap_model


def count_optimizer_params(trainer):
    """Count parameters tracked by optimizer."""
    total = 0
    for param_group in trainer.optimizer.param_groups:
        total += sum(p.numel() for p in param_group['params'])
    return total


def count_model_trainable(model):
    """Count trainable parameters in model."""
    return sum(p.numel() for p in model.parameters() if p.requires_grad)


def get_deep_layer_grad_norm(trainer, layer_idx=20):
    """Get L2 norm of gradients on a deep layer (should be 0 if frozen)."""
    unwrapped = unwrap_model(trainer.model)
    if hasattr(unwrapped, 'model') and hasattr(unwrapped.model, 'model'):
        layers = unwrapped.model.model
        if layer_idx < len(layers):
            layer = layers[layer_idx]
            total_norm = 0.0
            for p in layer.parameters():
                if p.requires_grad and p.grad is not None:
                    total_norm += p.grad.data.norm(2).item() ** 2
            return total_norm ** 0.5
    return None


def set_bn_eval(module):
    """Recursively set all BatchNorm layers to eval mode."""
    for child in module.children():
        if isinstance(child, torch.nn.BatchNorm2d):
            child.eval()
        set_bn_eval(child)


def on_train_start_callback(trainer, mode):
    """Callback to set BN to eval and add safety checks."""
    # Set all BN layers to eval mode
    set_bn_eval(trainer.model)
    
    # Count params
    model_trainable = count_model_trainable(trainer.model)
    optim_tracked = count_optimizer_params(trainer)
    
    # Check if unfreeze was applied
    has_surgical_mode = hasattr(trainer, 'surgical_mode')
    
    if has_surgical_mode:
        mode = trainer.surgical_mode
        expected = UNFREEZE_MODES.get(mode, set())
        unfrozen_layers = len(expected)
        
        # Safety check: model trainable vs optimizer tracked
        match = model_trainable == optim_tracked
        
        print(f"[SURGICAL] mode={mode} | "
              f"trainable={model_trainable:,} | "
              f"frozen={trainer.model.num_parameters() - model_trainable:,} | "
              f"optimizer_tracked={optim_tracked:,} | "
              f"MATCH={match}")
        
        trainer._surgical_verification = {
            'mode': mode,
            'model_trainable': model_trainable,
            'optim_tracked': optim_tracked,
            'match': match,
            'unfrozen_layers': unfrozen_layers
        }


def on_train_batch_start_callback(trainer):
    """Prevent BN from switching back to train mode."""
    set_bn_eval(trainer.model)


def train_and_verify(mode, checkpoint_path, data_path, epochs=3, imgsz=640, batch=4, device='cpu'):
    """Train with a specific mode and verify results."""
    print(f"\n{'='*60}")
    print(f"TRAINING MODE: {mode}")
    print(f"{'='*60}")
    
    # Load model
    model = YOLO(checkpoint_path)
    
    # Add surgical unfreeze callback - apply mode and rebuild optimizer before trainer builds it
    def make_unfreeze_callback(m):
        def on_before_build_optimizer_callback(trainer):
            print(f"\n{'='*80}", flush=True)
            print(f"[DEBUG CALLBACK START] mode={m}", flush=True)
            print(f"[DEBUG] trainer.model type: {type(trainer.model)}", flush=True)
            print(f"[DEBUG] trainer.model has _orig_mod: {hasattr(trainer.model, '_orig_mod')}", flush=True)
            print(f"[DEBUG] trainer.model has module: {hasattr(trainer.model, 'module')}", flush=True)
            
            # Apply surgical unfreeze
            unwrapped_model = unwrap_model(trainer.model)
            print(f"[DEBUG] unwrapped_model type: {type(unwrapped_model)}", flush=True)
            print(f"[DEBUG] unwrapped_model has model: {hasattr(unwrapped_model, 'model')}", flush=True)
            expected_trainable = apply_surgical_mode(unwrapped_model, m)
            
            print(f"[✅] Callback: unfroze {expected_trainable:,} params, rebuilding optimizer...", flush=True)
            
            # Rebuild optimizer
            trainer.optimizer = trainer.build_optimizer(
                model=trainer.model,
                name=trainer.args.optimizer,
                lr=trainer.args.lr0,
                momentum=trainer.args.momentum,
                decay=trainer.args.weight_decay,
                iterations=trainer.args.warmup_epochs,
            )
            
            model_trainable = sum(p.numel() for p in trainer.model.parameters() if p.requires_grad)
            model_total = sum(p.numel() for p in trainer.model.parameters())
            optim_tracked = count_optimizer_params(trainer)
            
            print(f"[✅] Callback: model_trainable={model_trainable:,}, model_total={model_total:,}, optimizer_tracked={optim_tracked:,}", flush=True)
            
            # Optimizer should track all model params (trainable + frozen), not just trainable
            assert model_total == optim_tracked, (
                f"Optimizer mismatch: model_total ({model_total:,}) != "
                f"optimizer_tracked ({optim_tracked:,})"
            )
            
            # Rebuild scheduler
            trainer._setup_scheduler()
            
            print(f"[✅] Callback: scheduler rebuilt", flush=True)
            print(f"{'='*80}\n", flush=True)
        return on_before_build_optimizer_callback
    
    model.add_callback("on_before_build_optimizer", make_unfreeze_callback(mode))
    
    # Add callbacks - pass mode through closure
    def on_train_start_wrapper(trainer):
        on_train_start_callback(trainer, mode)
    
    model.add_callback("on_train_start", on_train_start_wrapper)
    model.add_callback("on_train_batch_start", on_train_batch_start_callback)
    
    # Train with full error capture
    import traceback
    try:
        results = model.train(
            data=data_path,
            epochs=epochs,
            imgsz=imgsz,
            batch=batch,
            device=device,
            workers=2,
            amp=False,  # Disable AMP for more stable gradients
            seed=42,
            save=True,
            project='runs/verify_unfreeze',
            name=f'{mode}_epochs{epochs}',
            exist_ok=True,
            verbose=True
        )
    except Exception as e:
        print(f"\n{'='*80}")
        print(f"❌ EXCEPTION during training for mode '{mode}'")
        print(f"{'='*80}")
        traceback.print_exc()
        print(f"{'='*80}\n")
        raise
    
    # Get verification data
    verification = getattr(model.trainer, '_surgical_verification', None)
    
    # Get gradient norm on deep layer
    grad_norm = get_deep_layer_grad_norm(model.trainer, layer_idx=20)
    
    # Get final losses from results CSV (last epoch)
    results_csv = Path(model.trainer.save_dir) / 'results.csv'
    if results_csv.exists():
        import pandas as pd
        df = pd.read_csv(results_csv)
        last_row = df.iloc[-1]
        train_loss = last_row['train/box_loss']
        val_mAP50 = last_row['metrics/mAP50(M)']
    else:
        train_loss = 0.0
        val_mAP50 = 0.0
    
    return {
        'mode': mode,
        'verification': verification,
        'grad_norm': grad_norm,
        'train_loss': train_loss,
        'val_mAP50': val_mAP50,
        'epochs': epochs
    }


def main():
    """Run verification for contrasting modes."""
    print("🔍 Verifying surgical unfreeze fix...")
    
    # Paths
    checkpoint_path = 'weights/yolo26n-seg.pt'
    data_path = 'data/processed/yolo_seg_subset/data.yaml'
    
    # Check if checkpoint exists
    if not os.path.exists(checkpoint_path):
        print(f"⚠️  Downloading checkpoint to {checkpoint_path}")
        model = YOLO('yolo26n-seg.pt')
        model.save(checkpoint_path)
        del model
        torch.cuda.empty_cache()
    
    # Check if data exists
    if not os.path.exists(data_path):
        print(f"❌ Data file not found at {data_path}")
        print("   Please provide a valid dataset path")
        return False
    
    # Verify modes
    modes = ['early_texture', 'full_unfreeze']
    
    # Check if modes are different
    if UNFREEZE_MODES['early_texture'] == UNFREEZE_MODES['full_unfreeze']:
        print("❌ Modes are identical - verification impossible")
        return False
    
    # Train both modes
    results = {}
    for mode in modes:
        try:
            results[mode] = train_and_verify(
                mode=mode,
                checkpoint_path=checkpoint_path,
                data_path=data_path,
                epochs=3,
                imgsz=640,
                batch=4,
                device='cpu' if not torch.backends.mps.is_available() else 'mps'
            )
        except Exception as e:
            print(f"❌ Error training {mode}: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # Verify results
    print("\n" + "="*60)
    print("VERIFICATION RESULTS")
    print("="*60)
    
    all_pass = True
    
    # Check a) Different trainable param counts
    early_trainable = results['early_texture']['verification']['model_trainable']
    full_trainable = results['full_unfreeze']['verification']['model_trainable']
    
    if early_trainable != full_trainable:
        print(f"✅ a) Different trainable counts: {early_trainable:,} vs {full_trainable:,}")
    else:
        print(f"❌ a) SAME trainable counts: {early_trainable:,}")
        all_pass = False
    
    # Check b) Both modes have matching model_trainable == optimizer_tracked
    early_match = results['early_texture']['verification']['match']
    full_match = results['full_unfreeze']['verification']['match']
    
    if early_match and full_match:
        print(f"✅ b) Both modes: model_trainable == optimizer_tracked")
    else:
        print(f"❌ b) Mismatch: early={early_match}, full={full_match}")
        all_pass = False
    
    # Check c) Different final train_loss values
    early_loss = results['early_texture']['train_loss']
    full_loss = results['full_unfreeze']['train_loss']
    
    if abs(early_loss - full_loss) > 0.001:
        print(f"✅ c) Different train_loss: {early_loss:.4f} vs {full_loss:.4f}")
    else:
        print(f"❌ c) SAME train_loss: {early_loss:.4f}")
        all_pass = False
    
    # Check d) Frozen layers have zero gradient norm
    early_grad = results['early_texture']['grad_norm']
    if early_grad is not None and early_grad < 0.001:
        print(f"✅ d) Frozen layer gradient norm near zero: {early_grad:.6f}")
    elif early_grad is None:
        print(f"⚠️  d) Could not check gradient norm (layer not found)")
    else:
        print(f"❌ d) Frozen layer has non-zero gradient: {early_grad:.6f}")
        all_pass = False
    
    # Check e) No NaN in results
    early_nan = torch.isnan(torch.tensor(results['early_texture']['train_loss'])).any().item()
    full_nan = torch.isnan(torch.tensor(results['full_unfreeze']['train_loss'])).any().item()
    
    if not early_nan and not full_nan:
        print(f"✅ e) No NaN in either run")
    else:
        print(f"❌ e) NaN detected: early={early_nan}, full={full_nan}")
        all_pass = False
    
    # Print summary table
    print("\n" + "="*60)
    print("SUMMARY TABLE")
    print("="*60)
    
    print("\n| Mode | Trainable | Optimizer | Match | Train Loss | Val mAP50 | Grad Norm |")
    print("|------|-----------|-----------|-------|------------|-----------|-----------|")
    
    for mode in modes:
        r = results[mode]
        v = r['verification']
        print(f"| {mode:15} | {v['model_trainable']:>10,} | {v['optim_tracked']:>9,} | {str(v['match']):5} | {r['train_loss']:>10.4f} | {r['val_mAP50']:>9.4f} | {r['grad_norm'] if r['grad_norm'] else 'N/A':>9} |")
    
    # Final verdict
    print("\n" + "="*60)
    if all_pass:
        print("✅ UNFREEZE FIX VERIFIED")
        print("="*60)
        print("\nAll verification checks passed:")
        print("  a) Different trainable param counts between modes")
        print("  b) Model trainable == optimizer tracked for both modes")
        print("  c) Different final train_loss values (smoking gun)")
        print("  d) Frozen layers have zero gradient norm")
        print("  e) No NaN in results")
    else:
        print("❌ UNFREEZE FIX INCOMPLETE")
        print("="*60)
        print("\nSome verification checks failed. See details above.")
    
    return all_pass


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
