# Stage 2 Training Platform — Detailed Build Plan

## 0. Guiding principles

**What changes:**
- Training becomes a composition of four first-class entities: **Taxonomy → Checkpoint → Recipe → Chain**.
- The current one-shot `LaunchTrainingDialog` becomes a **strategy chooser**.
- Stage 2 is no longer hardcoded to 7 classes; the class list is an editable, saved entity.

**What stays (preserved from Phase 7):**
- `training_jobs` table + job list/detail UI + log streaming + config snapshotting + Mac safety guard.
- Experiment comparison (MLflow) module.
- Dataset prep (import / detect / resplit / tile).

**Critical constraint I'll honor:** Stage 1's trainer (`train.py` SOD variant) uses a **nested** config schema (`project.name`, `model.preset`, `pipeline.loss_type`), while Stage 2/3 trainers use a **flat** schema (`model_preset`, `loss_type`, `differential_lr`). The recipe engine must emit the correct shape per stage.

---

## 1. Entity model

```
Taxonomy ──┐
           ├──► Recipe ──► (one or more) Chain Steps ──► Chain
Checkpoint ┘        │
                    └──► single training Job
Surgery: Checkpoint(source) + Taxonomy(target) ──► Checkpoint(remapped)
```

- **Taxonomy**: an ordered, editable class list. Enables big-defect vs small-defect splits.
- **Checkpoint**: any `.pt` with lineage (native / trained / surgery).
- **Recipe**: a reusable training strategy bound to a taxonomy.
- **Chain**: ordered recipes where a step can consume the previous step's `best.pt`.

---

## 2. Database schema (SQLite)

New module `backend/services/platform_db.py` owns these tables. The existing `training_jobs` table gets new columns via an `ALTER TABLE` migration on startup.

### `taxonomies`
| Column | Type | Notes |
|---|---|---|
| id | TEXT PK | uuid |
| name | TEXT | e.g. "7-class defect", "big-defects", "small-defects" |
| stage | TEXT | stage1 / stage2 / stage3 |
| class_names | TEXT | JSON array, ordered, e.g. `["dent","scratch",...]` |
| description | TEXT | optional |
| created_at / updated_at | TEXT | ISO timestamps |

### `checkpoints`
| Column | Type | Notes |
|---|---|---|
| id | TEXT PK | uuid |
| name | TEXT | display name |
| path | TEXT | absolute path to `.pt` |
| origin | TEXT | `native_coco` \| `trained` \| `surgery` |
| source_checkpoint_id | TEXT FK | lineage (for surgery/trained) |
| source_job_id | TEXT FK | job that produced it |
| stage | TEXT | |
| nc | INTEGER | class count |
| class_names | TEXT | JSON (target classes for surgery outputs) |
| architecture | TEXT | e.g. `yolo26m-seg` |
| created_at / notes | TEXT | |

### `recipes`
| Column | Type | Notes |
|---|---|---|
| id | TEXT PK | |
| name | TEXT | |
| stage | TEXT | |
| taxonomy_id | TEXT FK | |
| description | TEXT | |
| base_strategy | TEXT | `native_coco` \| `from_checkpoint` \| `from_previous_step` |
| base_checkpoint_id | TEXT FK | nullable |
| freeze_mode | TEXT | `none` \| `freeze_n` \| `head_only` |
| freeze_layers | INTEGER | for `freeze_n` |
| lr_mode | TEXT | `uniform` \| `differential` |
| split_layer_idx | INTEGER | for differential |
| backbone_lr_mult | REAL | for differential |
| loss_type | TEXT | `bce` \| `focal` \| `ce` |
| fl_gamma / fl_alpha / fl_scale | REAL | focal params |
| imgsz / batch_size / epochs | INTEGER | |
| optimizer | TEXT | `auto`/`SGD`/`AdamW` |
| lr0 / lrf / patience | REAL/INT | |
| augmentations | TEXT | JSON (hsv, degrees, scale, mosaic, etc.) |
| is_preset | BOOLEAN | seeded template vs user-created |
| created_at | TEXT | |

### `chains` + `chain_steps`
| `chains` | | |
| id / name / stage / description / created_at | | |
| `chain_steps` | | |
| id | TEXT PK | |
| chain_id | TEXT FK | |
| order_index | INTEGER | execution order |
| recipe_id | TEXT FK | |
| dataset_id | TEXT | dataset to train on |
| base_source | TEXT | `recipe_default` \| `previous_step_best` \| `specific_checkpoint` |
| base_checkpoint_id | TEXT | nullable |

### `jobs` (extend existing `training_jobs`)
Add columns:
| Column | Notes |
|---|---|
| job_type | `training` \| `surgery` \| `chain_step` |
| recipe_id | nullable |
| chain_id / chain_step_index | nullable, for chain runs |
| parent_job_id | the job that produced this step's base |
| output_checkpoint_id | the checkpoint this job produced |

---

## 3. Phase A — Foundation: Taxonomy + Checkpoint Registry

### Backend
| File | Action | Contents |
|---|---|---|
| `backend/services/platform_db.py` | NEW | DB init, all tables, migration for `training_jobs` |
| `backend/schemas/taxonomy.py` | NEW | `Taxonomy`, `TaxonomyCreate`, `TaxonomyUpdate`, `TaxonomyListResponse` |
| `backend/schemas/checkpoint.py` | NEW | `Checkpoint`, `CheckpointListResponse` |
| `backend/services/taxonomy_service.py` | NEW | CRUD + validation (no duplicate class names, non-empty) |
| `backend/services/checkpoint_registry.py` | NEW | scan `runs/**/weights/*.pt` + root `.pt`, register native COCO, track lineage |
| `backend/api/taxonomy.py` | NEW | endpoints below |
| `backend/api/checkpoints.py` | NEW | endpoints below |
| `backend/main.py` | EXTEND | register 2 routers |

**API endpoints:**
```
GET    /api/taxonomies
POST   /api/taxonomies
GET    /api/taxonomies/{id}
PATCH  /api/taxonomies/{id}
DELETE /api/taxonomies/{id}
GET    /api/checkpoints
POST   /api/checkpoints/scan          # rescan filesystem
POST   /api/checkpoints/register      # manual register
GET    /api/checkpoints/{id}
DELETE /api/checkpoints/{id}
```

### Frontend
| File | Action |
|---|---|
| `src/lib/inspection/platformSchema.ts` | NEW — Taxonomy + Checkpoint types |
| `src/lib/inspection/apiClient.ts` | EXTEND — taxonomy + checkpoint fetch fns |
| `src/components/Platform/TaxonomyEditor.tsx` | NEW — add/remove/reorder classes, live preview |
| `src/components/Platform/TaxonomyList.tsx` | NEW |
| `src/components/Platform/CheckpointPicker.tsx` | NEW — reusable base-model selector |
| `src/components/Platform/CheckpointList.tsx` | NEW |
| `src/routes/models.tsx` | NEW — "Models" tab (taxonomies + checkpoints) |
| `src/routes/__root.tsx` | EXTEND — add "Models" nav link |

**Verify:** Create a 7-class taxonomy AND a 2-class "big-defects" taxonomy; see `yolo26m-seg.pt` + `yolo11n-seg.pt` auto-registered as `native_coco` checkpoints.

---

## 4. Phase B — Dataset Audit Gate

### Backend
| File | Action | Contents |
|---|---|---|
| `backend/schemas/dataset_audit.py` | NEW | `AuditReport`, `SizeBucket`, `LabelIssue` |
| `backend/services/dataset_audit.py` | NEW | full audit logic |
| `backend/api/dataset_audit.py` | NEW | endpoints |

**Audit computes:**
- Class distribution + per-class instance counts (reuse `dataset_registry._compute_class_distribution`)
- Image size buckets by annotation area: **bottom-10% / middle-50% / top-40%** (Commandment #1)
- Label validity: images missing labels, unparseable labels, class IDs out of range
- Empty-label count
- Leakage (reuse `run_leakage_audit`)
- Imbalance warnings (rare classes flagged)

**API:**
```
POST /api/datasets/{id}/audit/full     # run + cache report
GET  /api/datasets/{id}/audit/report
```

### Frontend
| File | Action |
|---|---|
| `src/components/Datasets/DatasetAuditReport.tsx` | NEW — size buckets, class balance, label issues, leakage |
| `src/components/Datasets/DatasetDetailPanel.tsx` | EXTEND — mount audit panel + "cleared for training" gate |

**Verify:** drop a ZIP → audit runs → report shows before any training is allowed.

---

## 5. Phase C — Head Surgery (UI action)

### Backend
| File | Action | Contents |
|---|---|---|
| `backend/services/surgery_service.py` | NEW | rebuild head for target `nc`, transfer backbone, skip shape-mismatched tensors |
| `backend/api/surgery.py` | NEW | endpoints |

**Surgery logic** (wraps your `remap_model1_head.py`):
1. Load source checkpoint, read its `model.yaml` config.
2. Copy config, set `nc` = target taxonomy size, drop old `names`.
3. Rebuild `SegmentationModel`.
4. Transfer matching weights; skip head tensors whose shapes mismatch.
5. Option toggle: **fresh head init** (default, your Model-5 approach) vs **class-aware copy**.
6. Save → register as new checkpoint with `origin=surgery`, lineage to source.

Runs as a background job (`job_type=surgery`) so the UI can show progress.

**API:**
```
POST /api/surgery                 # {source_checkpoint_id, taxonomy_id, head_init_mode}
GET  /api/surgery/{job_id}
```

### Frontend
| File | Action |
|---|---|
| `src/components/Surgery/HeadSurgeryDialog.tsx` | NEW — pick source checkpoint + target taxonomy + init mode → run → shows resulting checkpoint |

**Needs from you:** `src/stage2/Resume-and-Adapt/remap_model1_head.py`.

**Verify:** remap a checkpoint to a new class count → new checkpoint appears in registry with correct lineage + `nc`.

---

## 6. Phase D — Training Recipes + Strategy Presets

### Backend
| File | Action |
|---|---|
| `backend/schemas/recipe.py` | NEW |
| `backend/services/recipe_service.py` | NEW — CRUD + preset seeding |
| `backend/api/recipes.py` | NEW |

**API:**
```
GET    /api/recipes
GET    /api/recipes/presets
POST   /api/recipes
GET    /api/recipes/{id}
PATCH  /api/recipes/{id}
DELETE /api/recipes/{id}
```

### Seeded Strategy Presets (concrete values from your trainers)

| Preset | base | freeze | LR | loss | key params |
|---|---|---|---|---|---|
| **Direct from COCO** | native `yolo26m-seg` | none | uniform | bce | lr0=0.01, optimizer=auto |
| **Freeze Backbone** | checkpoint | `freeze_n` (N=15) | uniform | focal | fl_gamma=1.5, fl_alpha=0.5 |
| **Head-Only Warmup** | remapped ckpt | `head_only` (freeze=23) | uniform, lr0=0.005 | focal | gamma=2.0, alpha=0.5, imgsz=1024, batch=4, epochs=15 |
| **Differential LR Fine-tune** | warmup best.pt | none | `differential`, split_idx=23, backbone_mult=0.1, lr0=0.0003 | focal | imgsz=1024, batch=4, epochs=120, mosaic=0 |

Each preset pre-fills a recipe form; operator tweaks and saves as their own named recipe.

### Frontend
| File | Action |
|---|---|
| `src/components/Training/StrategyPresetPicker.tsx` | NEW — the 4 preset cards |
| `src/components/Training/RecipeBuilder.tsx` | NEW — full editable form (freeze, LR, loss, aug) |
| `src/components/Training/RecipeList.tsx` | NEW |

**Verify:** create recipes matching your three examples — COCO+Freeze15, Resume-Adapt DiffLR, Resume-Adapt Warmup@1024.

---

## 7. Phase E — Worker Redesign (execute a Recipe)

### Backend
| File | Action |
|---|---|
| `backend/services/training_worker.py` | REWORK — recipe-driven execution |

**New capability: `build_config_from_recipe(recipe, dataset, checkpoint) → dict`**
- Emits **flat schema** for Stage 2/3 (matches your production `train.py`).
- Emits **nested schema** for Stage 1 (matches your SOD `train.py`).
- Maps `freeze_mode` → `freeze` int; `lr_mode=differential` → `differential_lr`+`split_layer_idx`+`backbone_lr_mult`.
- Sets `model_preset` = checkpoint path.
- Preserves config snapshotting, log streaming, MLflow tags, Mac safety guard.

**Verify:** launch a recipe end-to-end; the snapshot YAML matches the recipe; correct trainer script is dispatched per stage.

**Needs from you:** current `training_worker.py`, `schemas/training.py`, `training_db.py` (so I rework precisely).

---

## 8. Phase F — Chains + Model Tracks + Launch Redesign

### Backend
| File | Action |
|---|---|
| `backend/schemas/chain.py` | NEW |
| `backend/services/chain_service.py` | NEW — sequential orchestration, `previous_step_best` handoff |
| `backend/api/chains.py` | NEW |

**Champion Chain Template (seeded):**
```
Chain: "Stage 2 Resume-and-Adapt Champion"
  Step 1: Surgery        source=model1.pt → target=7-class taxonomy
  Step 2: Head Warmup    base=step1.out, dataset=yolo_seg_clean_2200_7cls,
                          freeze=head_only, lr0=0.005, imgsz=1024, epochs=15
  Step 3: Diff-LR FT     base=step2.best.pt, dataset=yolo_seg_clean_2200_7cls,
                          differential, split_idx=23, lr0=0.0003, epochs=120
```

### Frontend
| File | Action |
|---|---|
| `src/components/Training/ChainBuilder.tsx` | NEW — add/reorder steps, set handoff |
| `src/components/Training/LaunchStrategyChooser.tsx` | NEW — replaces LaunchTrainingDialog: choose Direct / Recipe / Chain |
| `src/components/Training/ModelTracksView.tsx` | NEW — manage N parallel models per stage |
| `src/routes/training.tsx` | REWORK — strategy chooser + tracks |

### Multi-model support (big vs small defect)
This falls out naturally from first-class entities:
1. Create taxonomy **"big-defects"** = `[dent, glass_shatter, disjoint_part]` and **"small-defects"** = `[scratch, corrosion, crack]`.
2. Create a recipe/chain for each.
3. **Model Tracks view** shows both tracks side-by-side, each independently launchable and comparable.

**Verify:** one-click re-run of the champion chain; run two parallel tracks.

---

## 9. Phase G — Phase 3 Diagnostic-Driven Iteration

| Component | Purpose |
|---|---|
| `diagnostics/xray_service.py` | Raw-logits X-ray — bypass API, intercept logits pre-sigmoid/NMS; match activation to loss (Commandment #3) |
| `diagnostics/diagnosis_engine.py` | Classify failure: signal **absent** (≈0) → SAHI; **weak** (0.2–0.4) → focal; **strong** → threshold issue |
| `diagnostics/sahi_config.py` | SAHI inference: patch=640, overlap=15%, IOS NMS, conf=0.25, global-coord transform |
| `diagnostics/threshold_calibration.py` | Precision/Recall/F1 sweep 0.01–0.90, recall-optimized |
| `diagnostics/size_bucketed_recall.py` | Bottom-10% recall metric (Commandment #1) |
| `components/Diagnostics/*` | XRayPanel, DiagnosisPanel, CalibrationPanel, DiagnosticsDashboard |

Built after training platform is solid.

---

## 10. Master step order

```
A1 platform_db + tables        A2 taxonomy svc/api      A3 checkpoint svc/api     A4 taxonomy+checkpoint UI + Models tab
B1 audit svc                   B2 audit api             B3 audit report UI (gate)
C1 surgery svc                 C2 surgery api           C3 surgery dialog UI
D1 recipe schema/svc           D2 seed presets          D3 recipe UI
E1 worker redesign (recipe)    E2 verify recipe run
F1 chain svc/api               F2 seed champion chain   F3 launch chooser + model tracks
G1 xray  G2 diagnosis  G3 sahi  G4 calibration  G5 size-bucketed recall  G6 diagnostics UI
```

---

## 11. Files I'll need from you (at the right phase)

| Phase | File |
|---|---|
| C | `src/stage2/Resume-and-Adapt/remap_model1_head.py` |
| E | current `backend/services/training_worker.py`, `backend/schemas/training.py`, `backend/services/training_db.py` |
| D | one Stage 2 champion config (e.g. `configs/train/stage2/model5_*.yaml`) to confirm exact param names |

---

## 12. Open decisions (answer before Phase A)

1. **Execution target:** keep local subprocess (Mac/MPS) now, add Ubuntu-server dispatch later? *(my recommendation: yes)*
2. **Frontend folder:** new `src/components/Platform/` + `src/lib/inspection/platformSchema.ts`, or extend existing `Training/`? *(my recommendation: a `Platform/` folder for taxonomy+checkpoints, keep `Training/` for recipes/chains)*
3. **Surgery head init:** fresh-head-init as default, class-aware-copy as an optional toggle? *(my recommendation: yes)*
4. **DB location:** extend existing `training_jobs.db` with new tables, or a separate `platform.db`? *(my recommendation: extend the existing DB so jobs/recipes/checkpoints share one store)*
