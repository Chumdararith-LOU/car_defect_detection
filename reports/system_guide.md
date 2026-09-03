# System & Maintenance Guide — car_defect_detection

For developers and maintainers of the inspection backend and its model
ensemble. Every claim cites a file path. For calibration numbers see
[docs/reports/phase4_safety_calibration.md](../docs/reports/phase4_safety_calibration.md)
(linked, not duplicated here).

---

## 1. Architecture

Entry point: `POST /api/inspect` (`backend/api/inspect.py:31`), form fields
`stage2_mode` (default `sahi`), `stage2_preset` (default `safety`),
`device` (default `auto`), plus `enable_stage1/2/3` toggles
(`backend/api/inspect.py:36-42`).

Flow in `run_inspection` (`backend/services/__init__.py:26`):

1. **Stage 1 — pre-screen gate** (`backend/services/__init__.py:70-95`):
   `run_prescreen`; if `error` or `not is_active` it returns a PASS payload
   immediately and Stages 2-3 never run.
2. **Stage 2 — defect localization** (`backend/services/__init__.py:97-132`):
   mode `sahi` calls `run_sahi_inference` (`backend/services/stage2_sahi.py:57`);
   on any exception it falls back to `direct`
   (`backend/services/__init__.py:113-115`). Direct mode requires
   `stage2_model_name` and uses `run_direct_inference` via
   `model_manager.get_model` (`backend/services/__init__.py:117-132`).
3. **Stage 3 — panel segmentation** (`backend/services/__init__.py:134-146`):
   `run_panel_inference`; failures degrade to empty panels, never an error.
4. **Stage 4 — IoD fusion** (`backend/services/__init__.py:148-159`):
   `assign_defects_to_panels`, plus Stage-1 blob rescue
   (`rescue_unclassified_anomalies`, `extract_stage1_blobs`).
   Status is `FAIL` if defects or unclassified anomalies exist
   (`backend/services/__init__.py:161`).

**Device resolution**: `_resolve_device` (`backend/api/inspect.py:14-28`)
maps `auto` → `cuda` → `mps` → `cpu`; the orchestrator re-resolves via
`core/system_metrics.resolve_device` (`backend/services/__init__.py:8,43`).
The resolved device is injected into the response payload
(`backend/api/inspect.py:121-122`).

**Persistence**: every inspection is saved to `backend/data/inspections/`
via `save_inspection` (`backend/api/inspect.py:125-130`), with
collision-proof ids `INSP_<ts>_<uuid6>` (`backend/services/__init__.py:45`).

---

## 2. Multi-model ensemble

All ensemble behavior lives in `configs/inference/sahi_production.yaml`,
read once at import (`backend/services/stage2_sahi.py:22-29`).

- **model_registry** (`configs/inference/sahi_production.yaml:7-11`): name →
  weights path. Relative paths resolve against the project root
  (`backend/services/stage2_sahi.py:90-92`). Models are cached in-process
  (`_CACHED_MODELS`, `backend/services/stage2_sahi.py:44,93-100`).
- **routing_strategy per preset**
  (`configs/inference/sahi_production.yaml:20-50`): each preset lists
  `models` and a `merge` mode (`none`, `union`, `per_class`). Unknown
  presets default to `[objectness_branch_new]`/`none`
  (`backend/services/stage2_sahi.py:68-70`).
- **per_class merge** (`backend/services/stage2_sahi.py:166-177`): a class
  listed in `class_routing` is accepted ONLY from its designated model;
  undesignated classes keep detections from all models (union for recall).
  Current safety routing: corrosion+glass_shatter → `objectness_branch_new`;
  broken_part+disjoint_part → `baseline_m5`; crack/dent/scratch undesignated
  (`configs/inference/sahi_production.yaml:25-33`).
- **two-tier gating** (`configs/inference/sahi_production.yaml:52-57`):
  applies only to `applies_to: objectness_branch_new`; below
  `obj_threshold` a detection is dropped, between `obj_threshold` and
  `cls_threshold` it is relabeled `defect_unknown`
  (`backend/services/stage2_sahi.py:144-149`). Preset-level gating blocks
  override the global fallback (`backend/services/stage2_sahi.py:73-82`).
- **class_rules are name-keyed**
  (`configs/inference/sahi_production.yaml:59-121`, lookup at
  `backend/services/stage2_sahi.py:139-141`), with `CANONICAL_ALIASES`
  mapping legacy `broken_lamp` → `broken_part`
  (`backend/services/stage2_sahi.py:41-42`).

---

## 3. Taxonomy governance

Canonical 7 classes with semantic definitions (`AGENTS.md` §3.1):

| id | class | meaning |
|----|-------|---------|
| 0 | dent | panel deformation |
| 1 | scratch | surface abrasion |
| 2 | crack | fracture line |
| 3 | glass_shatter | broken glass |
| 4 | broken_part | damaged-but-attached component (lamps/mirrors/trim); models may emit legacy `broken_lamp`, aliased at the boundary |
| 5 | corrosion | oxidation/rust |
| 6 | disjoint_part | detached/missing part ONLY |

**Two class-order families exist**: alphabetical (`objectness_branch_new`,
`surgical_early`) and canonical (`baseline_m5`, `model_4`). The same class
has different raw ids per family (e.g. dent=0 canonical vs dent=3
alphabetical).

**Rule: resolve classes by NAME, never by raw id.** Name-keyed rules
(`backend/services/stage2_sahi.py:136-141`), name-keyed per_class routing
(`backend/services/stage2_sahi.py:169-175`), and NMS keys on `d["name"]`
(`backend/services/stage2_sahi.py:182-193`) — id-keyed logic previously
caused the threshold-swap incident and duplicate gallery cards. Per-model
names are read from the checkpoint itself
(`backend/services/stage2_sahi.py:110-113`); verify with
`scripts/dump_model_taxonomy.py`.

---

## 4. Config reference — `configs/inference/sahi_production.yaml`

| Key | Effect |
|-----|--------|
| `preset` (line 1) | default preset name |
| `model_type` (line 3) | SAHI backend type (`yolov8`) |
| `model_path` (line 4) | single-model path (legacy/direct use) |
| `device` (line 5) | default device hint |
| `model_registry` (7-11) | ensemble weights, name → path |
| `sahi.slice_size` (14) | slice edge; MUST match training resolution |
| `sahi.overlap_ratio` (15) | slice overlap (derived from O_min >= w/2P) |
| `nms.ios_threshold` (18) | mask Intersection-over-Smaller NMS threshold (0.50, thin-defect safe) |
| `routing_strategy.<preset>.models` | models loaded for the preset |
| `routing_strategy.<preset>.merge` | `none` / `union` / `per_class` |
| `routing_strategy.<preset>.class_routing` | class → designated model (per_class only) |
| `two_tier_gating.enabled/applies_to` | gating switch + target model |
| `two_tier_gating.obj_threshold/cls_threshold` | global fallback thresholds |
| `presets.<name>.class_rules` | per-class `{conf, min_area}`, name-keyed; `default` is the fallback |
| `presets.<name>.two_tier_gating` | per-preset threshold override |

Presets: `balanced`, `safety`, `max_recall`, `legacy_champion`, `specialist`
(production) and `calib` (sweep-only, never ship)
(`configs/inference/sahi_production.yaml:59-121`).

**The YAML is loaded once at module import
(`backend/services/stage2_sahi.py:28-29`) — restart the backend after ANY
edit.**

---

## 5. Calibration state

Final locked safety operating point (per_class routing + disjoint_part
conf 0.25, commit `f528c91`): **FPR 46.7% (70/150), Recall 94.3%
(559/593)** — full history, the voided pre-fix numbers, and the
disjoint_part sweep table are in
[docs/reports/phase4_safety_calibration.md](../docs/reports/phase4_safety_calibration.md).

- **FPR floor**: 22% of clean images emit >= 0.60-confidence hallucinations
  that no threshold can remove (structural; report §5).
- **Offline-vs-live divergence warning**: offline sweeps
  (`scripts/sweep_thresholds.py`, `scripts/sweep_routed_thresholds.py`)
  replay stored detections and CANNOT reproduce two-tier gating or routing
  as the live server runs them. Always confirm any threshold change with a
  live run (`scripts/preset_integration_test.py` or
  `scripts/sweep_disjoint_live.py`) before locking it.

---

## 6. Maintenance playbooks

### Add a model to the ensemble
1. Place weights under `runs/segment/<run>/weights/best.pt`.
2. Add `<name>: <path>` to `model_registry`
   (`configs/inference/sahi_production.yaml:7-11`).
3. Check its class order: `conda run -n car_defect python scripts/dump_model_taxonomy.py`.
4. Reference it in a preset's `routing_strategy.<preset>.models` (and
   `class_routing` if designated).
5. Restart the backend; verify with `scripts/test_mps_integration.py`.

### Add / rename a class
1. Update canonical names everywhere by NAME, never id:
   `class_rules` keys (`configs/inference/sahi_production.yaml`),
   `CANONICAL_ALIASES` if it is a legacy rename
   (`backend/services/stage2_sahi.py:41-42`), `_DEFAULT_CLASS_NAMES`
   (`backend/services/stage2_sahi.py:31-39`), frontend labels.
2. Update `AGENTS.md` §3.1 taxonomy.
3. Re-run a live preset measurement (see below).

### Recalibrate a preset (collect → sweep → live verify)
1. **Collect**: `scripts/collect_calibration_detections.py` (raw detections
   over the calibration set) or
   `scripts/collect_routed_safety_detections.py` (routed ensemble at low
   thresholds).
2. **Sweep offline** (candidate thresholds only):
   `scripts/sweep_thresholds.py` or `scripts/sweep_routed_thresholds.py`.
   For a live class-conf sweep use `scripts/sweep_disjoint_live.py` as the
   template.
3. **Live verify**: `conda run -n car_defect python scripts/preset_integration_test.py --preset <name> --limit 0`
   — this is the ground truth; lock numbers only from this run.
4. Record the operating point in
   `docs/reports/phase4_safety_calibration.md` and update the calibration
   comment in `configs/inference/sahi_production.yaml`.

### Restart procedure
The server runs from `backend/` (imports are backend-relative,
`backend/main.py:4-24`):

```bash
pkill -f "uvicorn" || true; sleep 2
cd backend && nohup conda run -n car_defect uvicorn main:app --port 8010 > ../server.log 2>&1 & disown
sleep 15 && curl -s -o /dev/null -w "%{http_code}" http://localhost:8010/docs   # expect 200
```

Then smoke-test: `conda run -n car_defect python scripts/test_e2e_api.py`.

---

## 7. Scripts inventory

| Script | Purpose |
|--------|---------|
| `scripts/collect_calibration_detections.py` | Collect raw detections from test + clean images for threshold calibration |
| `scripts/collect_routed_safety_detections.py` | Collect routed safety ensemble detections at low thresholds for sweeping |
| `scripts/diagnose_obj_logits.py` | Verify obj_logits extraction from Segment26WithObjectness via direct forward pass |
| `scripts/dump_model_taxonomy.py` | Dump the class taxonomy of every model in the SAHI model_registry |
| `scripts/preset_integration_test.py` | Run a production preset over the calibration set; image-level FPR/recall (live ground truth) |
| `scripts/setup_models.py` | Download and verify champion models for a fresh clone (sha256-checked, `configs/models/champion_models.json`) |
| `scripts/sweep_disjoint_live.py` | Live sweep of safety disjoint_part conf over the full calibration set |
| `scripts/sweep_routed_thresholds.py` | Sweep per-class confidence thresholds on routed-safety detections (offline) |
| `scripts/sweep_thresholds.py` | Sweep two-tier gating thresholds offline; image-level FPR and recall |
| `scripts/test_e2e_api.py` | End-to-end API smoke test: POST /api/inspect with defaults |
| `scripts/test_mps_integration.py` | Quick MPS integration test for the multi-model SAHI pipeline |

---

## 8. Known limits & roadmap

- **FPR floor (46.7%)**: structural — 22% of clean images produce
  >= 0.60-confidence hallucinations immune to thresholds
  (`docs/reports/phase4_safety_calibration.md` §5). Closing it requires
  hard-negative mining + retraining with more clean data (currently blocked
  on retraining server availability).
- **specialist / max_recall presets**: `specialist` shares the contamination
  fix (broken_part/disjoint_part → baseline_m5,
  `configs/inference/sahi_production.yaml:40-50`) but was never re-measured
  live; `max_recall` (4-model union, lines 34-36) predates the name-keyed
  fixes. Both need live re-validation before use.
- **Retention policy**: inspections accumulate in
  `backend/data/inspections/` with no automatic expiry. Deleting a batch
  deletes its member inspections (`backend/api/batches.py:54-72`), but
  standalone inspections persist indefinitely — define and implement a
  retention/TTL policy.
- **`calib` preset** (`configs/inference/sahi_production.yaml:109-121`) is
  sweep-only — never expose it in production UIs.
