# Stage 2 Retraining Plan

Based on the STAGE2_RETRAIN_BRIEF.md and AGENTS.md constraints, here is a comprehensive retraining plan for producing the best possible Stage 2 model:

## 1. Plan Overview

This plan addresses the objective of beating Model 5 (65.0% test Mask mAP50) while improving performance on weak classes (corrosion, disjoint_part) and reducing clean-image false-positives.

## 2. Implementation Priority

### Phase 1: Core Infrastructure (Immediate)
1. **Data pipeline enhancement**
   - Implement class mapping for unified 7-class taxonomy
   - Add deduplication logic
   - Integrate clean image handling with configurable negative ratio
   - Update data configuration files

2. **Evaluation metrics enhancement**
   - Add clean-image false-positive rate tracking
   - Implement per-class Mask mAP50 reporting
   - Add size-bucketed Mask mAP (tiny, small, medium)
   - Create comprehensive evaluation script

### Phase 2: Key Improvements (Sequential)
3. **Hard-negative injection**
   - Source clean car images from CarDD undamaged set + Kaggle "whole" class
   - Configure negative ratio sweep (10-15% of training images)
   - Verify no leakage between training and clean sets

4. **Class-balanced sampling**
   - Implement oversampling for corrosion/disjoint_part classes
   - Add weighted sampler or loss weighting for rare classes
   - Evaluate using SeeSaw/Equalization loss approach

5. **Gradual backbone unfreeze**
   - Try unfreezing last 1-2 backbone blocks
   - Implement progressive unfreezing approach
   - Compare against frozen baseline

6. **Native-resolution training**
   - Implement 1024px tile training with defect-containing crop oversampling
   - Modify training data pipeline to use SAHI-style crops

### Phase 3: Advanced Techniques (If needed)
7. **Copy-paste augmentation**
   - Apply synthetic corruption augmentation for rare classes
   - Evaluate CrashCar101 synthetic dataset

8. **Tiny-object loss surgery**
   - Patch Ultralytics assigner/loss code for better tiny defect handling
   - Address instability in corrosion-size range objects

## 3. Training Configuration Strategy

### 3.1 Baseline Configuration
- Use `configs/train/yolo26s-seg.yaml` as starting point
- Keep resolution at 1024×1024 (matching SAHI inference)
- Default: frozen-backbone + extended head-only warmup (as per locked decision)

### 3.2 Experiment Sweep Parameters
- **Clean-negative ratio**: 10-15% swept
- **Backbone unfreezing**: frozen (baseline), last 2 blocks, progressive
- **Sampling strategy**: balanced, oversampled, weighted
- **Training resolution**: 1024px base frame, 1024px tiles for enhancement

## 4. Benchmarking Protocol

### 4.1 Standard Metrics
- Report Mask mAP50 / mAP50-95 / Precision / Recall (Val and Test)
- Per-class Mask mAP50 (not just aggregate)
- Size-bucketed Mask mAP (tiny, small, medium)

### 4.2 New Metrics Required
- **Clean-image false-positive rate**: 
  - Run model over held-out clean car slice
  - Report % of images with ≥1 defect prediction above threshold
  - Breakdown by most hallucinated class

### 4.3 Run Logging
All training runs will be logged in the format:
```
[config] → [metrics] → [one-line verdict]
```

## 5. Deliverables Timeline

### Week 1-2:
1. Complete DATASET_AUDIT.md and unified taxonomy mapping
2. Enhance training data pipeline 
3. Implement new evaluation metrics
4. Source and prepare clean image datasets

### Week 3-4:
1. Implement hard-negative injection with configurable ratio
2. Run baseline experiments with current model
3. Begin class-balanced sampling experiments
4. Test gradual backbone unfreezing

### Week 5-6:
1. Full native-resolution training pipeline
2. Evaluate copy-paste augmentation
3. Assess tiny-object loss surgery
4. Final model selection and recommendation

## 6. Risk Mitigation

### 6.1 Technical Risks
- **Resolution mismatch**: Already locked at 1024px for both training and inference
- **Overfitting**: Use cross-validation and early stopping
- **Loss instability**: Gradual learning rate scheduling

### 6.2 Data Risks
- **Negative leakage**: Ensure strict train/val/test split separation
- **Domain shift**: Use CarDD's own undamaged set for domain consistency
- **Class imbalance**: Implement multiple balancing strategies

## 7. Resource Requirements

### 7.1 Compute Resources
- Training on single GPU recommended initially
- Model checkpoints for all intermediate experiments
- Storage for cleaned and consolidated datasets

### 7.2 Data Processing
- Label resolution and class mapping scripts  
- Deduplication processing pipeline
- Clean image sourcing and validation

This plan is designed to be iterative and focused on the specific issues identified in the brief. The emphasis on hard-negative injection addresses the key weak point identified in the current model performance.