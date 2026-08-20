# Backend API Error Handling Audit Report

Scope: all 21 Python files in `backend/api/` (read-only audit, no code changes).
Focus: endpoints that return generic 500 errors instead of proper 4xx responses, or fail to validate user input.

---

## Files with flaws

### 1. `backend/api/experiments.py`

| Function | Lines | Flaw |
|---|---|---|
| `api_list_experiments` | 23-33 | Catches broad `Exception` -> generic 500. An unknown/invalid MLflow tracking URI or missing experiment is a configuration/input problem surfaced as 500; no 4xx mapping. |
| `api_list_runs` | 36-44 | Catches broad `Exception` -> generic 500. An invalid/nonexistent `experiment_id` should be 404, but any lookup failure becomes 500. |
| `api_compare_runs` | 51-77 | Catches broad `Exception` -> generic 500. Unknown `run_ids` in `compare_runs()` should be 404/422; only empty-list and >10 cases are validated (400). |

### 2. `backend/api/inspect.py`

| Function | Lines | Flaw |
|---|---|---|
| `inspect_vehicle` | 31-142 | Catches broad `Exception` -> generic 500 (lines 137-142). Bad user input (corrupt/non-image upload via `process_uploaded_image`, invalid `stage2_preset`, invalid `stage2_mode`, bad `stage2_conf` range) all surface as 500 instead of 400/422. No file-type/content validation before processing. |
| `inspect_vehicle` | 64-78 | When Stage 1 model is missing, silently returns a MOCK PASS payload (200) instead of an error status — error condition swallowed as a success response. |

### 3. `backend/api/training.py`

| Function | Lines | Flaw |
|---|---|---|
| `launch_training_job` | 85-103 | Catches broad `Exception` -> generic 500 (line 101-103). Re-raises `HTTPException` correctly (good), but invalid `dataset_path` pointing to a nonexistent YAML, bad config values, or missing checkpoint files raised by `worker.launch` become 500 rather than 400/422. |
| `_resolve_recipe_config` | 20-82 | Maps `LookupError` for missing checkpoint to 422 (lines 64-67) — acceptable, but a missing-file checkpoint (`exists` false) is also 422; arguably 409/404. Minor. |

### 4. `backend/api/dataset_import.py`

| Function | Lines | Flaw |
|---|---|---|
| `api_import_inspection` | 70-85 | Catches broad `Exception` -> generic 500. A nonexistent `dataset_id` or `inspection_id` that raises something other than `ValueError` (e.g. `FileNotFoundError`, `KeyError`) becomes 500 instead of 404. |
| `api_upload_image` | 88-108 | Catches broad `Exception` -> generic 500. Missing dataset id raising non-`ValueError` becomes 500 instead of 404; no image content-type validation. |
| `api_create_dataset` | ~110-136 | Catches broad `Exception` -> generic 500. Duplicate dataset name or invalid class list raising non-`ValueError` becomes 500 instead of 409/400. |
| `api_import_zip` | 144-166 | Catches broad `Exception` -> generic 500. A nonexistent `dataset_id` or malformed zip raising non-`ValueError` (e.g. `BadZipFile`, `FileNotFoundError`) becomes 500 instead of 400/404. |

### 5. `backend/api/dataset_prep.py`

| Function | Lines | Flaw |
|---|---|---|
| `api_import_dataset` | 16-31 | Catches broad `Exception` -> generic 500. Malformed zip (`BadZipFile`) becomes 500 instead of 400. |
| `api_split_structure` | 34-43 | Catches broad `Exception` -> generic 500 (ValueError -> 404 is fine). |
| `api_resplit_dataset` | 46-~59 | Catches broad `Exception` -> generic 500; invalid split ratios or missing dataset raising non-`ValueError` become 500. |
| `api_tile_dataset` | ~62-86 | Catches broad `Exception` -> generic 500; nonexistent source dataset raising non-`ValueError` becomes 500 instead of 404. |

### 6. `backend/api/dataset_images.py`

| Function | Lines | Flaw |
|---|---|---|
| `api_list_images` | 21-30 | No error handling at all — invalid `dataset_id` likely raises unhandled `FileNotFoundError`/`ValueError` -> raw 500 from FastAPI instead of 404. |
| `api_get_labels` | 46-62 | No error handling — nonexistent dataset/image raises unhandled exception -> raw 500 instead of 404. |
| `api_reclassify_annotation` | 74-96 | Catches broad `Exception` -> generic 500; nonexistent dataset/file/index raising non-`ValueError` becomes 500 instead of 404. |
| `api_delete_annotation` | 99-121 | Same pattern — broad `Exception` -> generic 500 instead of 404 for missing resources. |

### 7. `backend/api/datasets.py`

| Function | Lines | Flaw |
|---|---|---|
| `api_delete_dataset` | 51-61 | Catches broad `Exception` -> generic 500; nonexistent dataset raising non-`ValueError` becomes 500 instead of 404. |
| `api_build_dataset` | 64-91 | Catches broad `Exception` -> generic 500; bad stage/version input raising non-`ValueError` becomes 500 instead of 400/422. |

### 8. `backend/api/dataset_audit.py`

| Function | Lines | Flaw |
|---|---|---|
| `run_full_audit` | 16-21 | Maps `KeyError` and `ValueError` to 404 ("dataset not found"), but these may indicate malformed audit data, not a missing dataset — inaccurate status semantics; truly unexpected errors still fall through as raw 500. Minor. |

### 9. `backend/api/models.py`

| Function | Lines | Flaw |
|---|---|---|
| `get_models` | 33-59 | No error handling — if `model_manager.list_available_models()` raises (missing models dir), unhandled exception -> raw 500. Minor (no user input involved). |

### 10. `backend/api/system.py`

| Function | Lines | Flaw |
|---|---|---|
| `get_system_metrics` / device listing | 13-73 | Silently swallows all `Exception` around torch/GPU detection (`pass`, lines 70-71) — acceptable for optional hardware probing, but hides real errors (e.g. broken torch install) with no logging. Minor. |

### 11. `backend/api/host.py`

| Function | Lines | Flaw |
|---|---|---|
| `get_host_profile` | 9-11 | No error handling — any failure in `detect_host_profile()` becomes a raw 500. Minor (no user input). |

---

## Files with clean error handling (no flaws found)

- `backend/api/batches.py` — ValueError mapped to 400/404, missing-resource checks return 404.
- `backend/api/chains.py` — LookupError -> 404, ValueError -> 422 consistently.
- `backend/api/checkpoints.py` — specific exceptions mapped to 404/409.
- `backend/api/model_registry.py` — None checks -> 404, result-message checks -> 404.
- `backend/api/recipes.py` — LookupError -> 404, PermissionError -> 409, ValueError -> 422.
- `backend/api/reviews.py` — None checks -> 404, empty-update -> 400.
- `backend/api/surgery.py` — (LookupError, KeyError) -> 404, ValueError -> 422.
- `backend/api/taxonomy.py` — specific exceptions mapped to 404/409/422.
- `backend/api/health.py` — trivial endpoint, no error handling needed.

---

## Summary of recurring patterns

1. **`except Exception` -> generic 500** is the dominant anti-pattern (experiments, dataset_import, dataset_prep, datasets, dataset_images reclassify/delete, training launch, inspect). Missing-resource failures (`FileNotFoundError`, `KeyError`) are lumped into 500 instead of 404.
2. **No input/resource validation before use** in `dataset_images.api_list_images` and `api_get_labels` — unhandled exceptions surface as raw FastAPI 500s.
3. **Silent success on error state**: `inspect.py` returns a mock PASS payload when the Stage 1 model is unavailable instead of a 503/4xx.
4. **Best-in-repo pattern** (used by chains/checkpoints/recipes/taxonomy/surgery): raise domain-specific exceptions in the service layer and map each to the correct 4xx HTTPException. Recommend applying this pattern to the flawed files.

---
---

# SQLite Thread-Safety Audit (backend/services)

Scope: `training_db.py`, `model_registry_db.py`, `review_db.py`.
Context: FastAPI serves sync endpoints in a threadpool (~40 threads by default) and the training worker runs background threads. All three modules are process-wide singletons imported by API routers, so concurrent access is a real scenario.

---

## 1. `backend/services/training_db.py`

**Connection model:** one shared `sqlite3.Connection` created in `__init__` (line 14) with `check_same_thread=False`, held for the process lifetime.

| Issue | Location | Detail |
|---|---|---|
| Shared connection with no lock | line 14, all methods | `check_same_thread=False` only disables the safety check; it does not make the connection thread-safe. Concurrent calls from API request threads and training-worker threads (`create_job`, status updates, `list_jobs`, `count_jobs`) share one connection/cursor with no `threading.Lock`. This can trigger `ProgrammingError: recursive use of cursors not allowed`, interleaved statements, or corrupted/partial reads. |
| Writes not serialized | `_create_tables`/`_migrate` (lines 19-62) and write methods use `with self.conn:` | `with conn:` only commits/rolls back the transaction; it provides no mutual exclusion. Two threads updating the same job (e.g. worker status callback + API stop) can interleave. |
| Connection never closed | line 14 | No `close()` or shutdown hook. Acceptable for a process-lifetime singleton, but if `_migrate()` raises, the connection is left open and there is no cleanup path. |

**Race condition risk: HIGH** — this is the most dangerous of the three. Any concurrent `list_jobs` during a worker status update can hit cursor errors or read partial state.

---

## 2. `backend/services/model_registry_db.py`

**Connection model:** new connection per call via `_connect()` (lines 37-40), always used as `with self._connect() as conn:`.

| Issue | Location | Detail |
|---|---|---|
| **Connection leak on every call** | `_connect()` + every `with` block (insert line 42, and all other methods) | `with conn:` on a sqlite3 connection manages the *transaction* (commit/rollback) only — it does **NOT** close the connection. Every method call leaks a connection until GC. Under load this exhausts file descriptors and causes `sqlite3.OperationalError: database is locked`. Needs `contextlib.closing()` or explicit `conn.close()` in `finally`. |
| Non-atomic check-then-act | promote/deploy flow (`get_champion` / `get_by_id` then insert/update on separate connections) | No lock and separate connections per call mean two concurrent promotions for the same stage could both read the old state and both write champion status -> two champions or a lost update (TOCTOU). |
| Default journal mode, no WAL | `_connect()` | Default rollback journal: readers block writers. Combined with leaked connections that may hold locks, contention is amplified. |

**Race condition risk: MEDIUM** (traffic is low today, but promote/deploy transitions are not atomic).
**Resource leak: HIGH** — every single call leaks a connection.

---

## 3. `backend/services/review_db.py`

**Connection model:** same per-call pattern as model_registry_db (lines 45-48).

| Issue | Location | Detail |
|---|---|---|
| **Connection leak on every call** | `_connect()` + all `with self._connect()` blocks (lines 42, 51, 95, and reads) | Same sqlite3 `with` semantics flaw — transactions are committed but connections are never closed. |
| TOCTOU in `update_review` | lines 83-97 | `get_review()` (connection A) then UPDATE (connection B). If the row is deleted between the check and the update, the UPDATE silently affects 0 rows and the final `get_review` returns None — caller gets an inconsistent result instead of a 404-equivalent signal. |
| Insert + readback | `insert_review` lines 50-56 | INSERT + SELECT readback happen within one connection/transaction — acceptable, since SQLite serializes writers. |

**Race condition risk: LOW** (low write volume).
**Resource leak: HIGH** — same leak pattern as model_registry_db.

---

## Cross-cutting summary

| Module | Connection mgmt | Locks | Transactions | Leaks | Race risk |
|---|---|---|---|---|---|
| `training_db.py` | Single shared conn, `check_same_thread=False` | None | `with conn:` (commit only) | No (persistent, but never closed) | **High** — shared conn unsynchronized |
| `model_registry_db.py` | Per-call connections | None | `with conn:` (commit only) | **Yes — every call** | Medium — non-atomic promote/deploy |
| `review_db.py` | Per-call connections | None | `with conn:` (commit only) | **Yes — every call** | Low — TOCTOU in `update_review` |

### Top recommendations

1. **`training_db.py`:** add a `threading.Lock` and wrap every use of `self.conn` (smallest safe fix), or switch to per-call connections after fixing the leak pattern below.
2. **`model_registry_db.py` / `review_db.py`:** wrap connections with `contextlib.closing(...)` (or `try/finally: conn.close()`) — `with conn:` alone leaks every connection.
3. Enable WAL (`PRAGMA journal_mode=WAL`) in all three modules to reduce reader/writer blocking.
4. Make multi-step lifecycle transitions (promote/deploy, job status updates) atomic within a single transaction or guarded by a lock.

---
---

# Stage 4 Spatial Fusion — Shapely Geometry Edge-Case Audit

Scope: `backend/services/stage4.py` (452 lines), plus DSI producers `stage2_direct.py:61` and `stage2_sahi.py:140`, and the orchestrator call sites in `backend/services/__init__.py:143-150`.
Focus: empty/invalid polygons, zero-area intersections, ZeroDivisionError, TopologyException, and IoD/DSI math correctness.

---

## What is handled well (no flaws)

- **`_to_polygon` (lines 47-57)** — central polygon builder is defensive: wraps construction in `try/except Exception -> None`, repairs invalid polygons via `buffer(0)`, and rejects empty/zero-area results. All IoD divisions therefore operate on geometries with `area > 0`, preventing most ZeroDivisionErrors.
- **`compute_iod` (lines 60-69)** — division by `defect.area` is safe because `_to_polygon` guarantees `area > 0`; exceptions fall back to 0.0. (Note: this function is dead code — never called anywhere.)
- **`rescue_unclassified_anomalies` line 283** — IoS guarded with `if smaller > 0 else 0.0`.
- **All `.intersection().area / area` sites** (lines 157, 170, 197, 204, 281, 316, 336, 344, 422) are wrapped in `try/except Exception` with 0.0 fallback, so most GEOS/TopologyExceptions are contained.
- **Clipping path (lines 425-428)** — checks `is_empty or area <= 0` and unwraps MultiPolygon to the largest part before use.

---

## Flaws found

### 1. DSI is never actually computed — spec violation (HIGH)

| Location | Detail |
|---|---|
| `assign_defects_to_panels`, lines 220-225 | When a defect is assigned to a real panel (`panel_id != "Unknown"` and panels exist), the code only does `assigned_count += 1` — it **never computes or sets `damage_severity_index_dsi`**. The AGENTS.md spec requires `DSI% = Area(defect) / Area(panel) * 100`. |
| `stage2_direct.py:61`, `stage2_sahi.py:140` | Because Stage 4 never overwrites DSI for assigned defects, the frontend receives the Stage 2 placeholder `min(0.99, pixel_area / 5000.0)` — an arbitrary heuristic unrelated to panel area. |
| Inconsistent semantics | DSI = `None` when no panels (line 221), `0.0` for "Unknown" panel (line 223), stale placeholder for assigned panels. Three different meanings for one field. |

### 2. Unhandled `AttributeError` in `extract_stage1_blobs` — crash path (HIGH)

| Location | Detail |
|---|---|
| Line 433: `coords = list(use_shape.exterior.coords)[:-1]` | Not inside any try/except. `.exterior` only exists on `Polygon`. If `_to_polygon`'s `buffer(0)` repair returns a **MultiPolygon** (possible for a self-intersecting figure-eight contour, since `_to_polygon` does not check geometry type or re-validate after `buffer(0)`), or if clipping yields a **GeometryCollection**, `.exterior` raises `AttributeError` -> propagates through `run_inspection` -> generic 500 on the `/api/inspect` endpoint. |
| Line 427-428 | MultiPolygon is unwrapped, but GeometryCollection (`geom_type == "GeometryCollection"`) is not handled and falls through to line 433 with `use_shape = clipped`. |

### 3. `build_car_context` geometry ops unprotected (MEDIUM)

| Location | Detail |
|---|---|
| Lines 116-118: `unary_union(all_polys)` and `union.buffer(d).buffer(-d)` | Not wrapped in try/except. Pathological panel polygons (near-degenerate, self-touching rings) can raise `GEOSException`/`TopologyException` here. None of the three callers (`assign_defects_to_panels:143`, `rescue_unclassified_anomalies:256`, `extract_stage1_blobs:403`) wrap the call either -> crash. |
| Line 126: `tire_mask = unary_union(tire_polys)` | No validity/emptiness check on the result (unlike `car_context` at 119-120). Downstream divisions are protected, but an invalid tire_mask can still trigger caught-but-silent 0.0 fallbacks that change suppression decisions. |

### 4. Degenerate bbox causes silent false suppression (MEDIUM)

| Location | Detail |
|---|---|
| Lines 191-200 | `shapely_box(float(bbox[0]) ...)` with a zero-area bbox (x1==x2 or y1==y2) or inverted bbox (x1>x2) yields area 0 or an invalid box. The division `bbox_shape.intersection(car_context).area / bbox_shape.area` raises `ZeroDivisionError`/`GEOSException`, which is caught -> `car_iod = 0.0` -> defect **suppressed as `non_car_context`** (line 209-210) instead of falling back to the polygon-based IoD in the else branch. Wrong output, not a crash — harder to detect. |

### 5. `_to_polygon` can return non-Polygon geometries (MEDIUM)

| Location | Detail |
|---|---|
| Lines 50-55 | After `buffer(0)`, the result type is not checked. `buffer(0)` may return `MultiPolygon` or `GeometryCollection`; these pass the `is_empty`/`area > 0` checks and flow into every downstream consumer. Intersection arithmetic survives (wrapped), but `.exterior` access (flaw #2) does not. Fix: extract the largest Polygon part or reject non-Polygon results. |

### 6. Dead/misleading API surface (LOW)

| Location | Detail |
|---|---|
| Line 60 `compute_iod` | Defined but never called (grep confirms zero call sites). |
| Line 130 `iod_threshold=0.1` parameter | Never read inside `assign_defects_to_panels`; the real threshold is the global `CONTAINMENT_THRESHOLD = 0.50` (line 213), which matches AGENTS.md `theta_containment = 0.50`. The unused parameter invites confusion. |

### 7. Minor: normalization divisions (LOW)

| Location | Detail |
|---|---|
| Lines 271, 415 | `float(p[0]) / img_w` — would raise ZeroDivisionError on a zero-dimension mask, but `cv2.findContours` on an empty mask returns `[]` (handled at 248/393) before normalization, so this is unreachable in practice. |

---

## Summary

| Category | Count | Verdict |
|---|---|---|
| ZeroDivisionError risk | 1 real (degenerate bbox, caught but wrong behavior) | Divisions mostly safe due to `area > 0` guards |
| TopologyException risk | Contained at all `.intersection()` sites; **uncontained** in `build_car_context` (unary_union/buffer) | Medium |
| Crash paths | `extract_stage1_blobs:433` `.exterior` on non-Polygon geometry | High |
| Spec violations | DSI formula never implemented; Stage 2 placeholder leaks to frontend | High |
| Silent wrong results | Degenerate bbox -> false `non_car_context` suppression | Medium |

### Top recommendations

1. **Implement DSI per spec** in `assign_defects_to_panels`: `dsi = defect_shape.intersection(panel_shape).area / panel_shape.area * 100` for the assigned panel.
2. **Guard `extract_stage1_blobs:433`**: coerce `use_shape` to a single Polygon (handle MultiPolygon/GeometryCollection) or wrap in try/except with `continue`.
3. **Harden `_to_polygon`**: after `buffer(0)`, if result is MultiPolygon take the largest part; if GeometryCollection extract polygonal parts; re-check `is_valid`.
4. **Wrap `build_car_context`** union/buffer in try/except returning `(None, None)`.
5. **Fall back to polygon IoD** when the bbox is degenerate (area <= 0 or inverted) instead of suppressing.
6. Remove dead `compute_iod` and the unused `iod_threshold` parameter (or wire it up).

---
---

# Training Worker Subprocess Management Audit

Scope: `backend/services/training_worker.py` (271 lines). Context: process-wide singleton `worker` (line 271) invoked from `api/training.py:97,167` and `chain_service.py:225`. Each job runs `subprocess.Popen` on a `daemon=True` background thread.

---

## Direct answers

### Are zombie processes possible if the FastAPI server crashes?

- **Zombies: no** under normal operation — `process.wait()` (line 164) reaps each child, and `finally` pops the registry entry (line 202).
- **Orphans: YES — this is the real risk.** Job threads are `daemon=True` (line 254). On graceful shutdown or crash, daemon threads die instantly and **nothing ever calls `terminate()` on the subprocess** (no atexit/lifespan hook). The training process survives the server, holding GPU/VRAM, re-parented to PID 1.
- **No startup reconciliation:** after a restart, `active_processes` is empty while the DB still shows those jobs as `RUNNING` forever — they can't be stopped via `/api/training/jobs/{id}/stop` and pollute the job list.
- **No process group:** `Popen` lacks `start_new_session=True`, so even a successful `terminate()` kills only the direct python child; grandchildren (e.g. DataLoader workers) can be orphaned.

### Is log streaming blocking the event loop?

- **No.** stdout/stderr are redirected straight to the log file (line 159) — Python never reads the pipes, so there is no pipe-buffer deadlock and no per-line streaming work. `process.wait()` runs on a background thread, and the launching endpoints are sync (FastAPI threadpool), so the asyncio event loop is untouched. (Note: the module docstring's "streams logs" is aspirational — no streaming is implemented.)

---

## Flaws found

| # | Severity | Location | Flaw |
|---|---|---|---|
| 1 | HIGH | line 254 (`daemon=True`), whole class | No shutdown hook terminates children -> orphaned training processes (with GPU memory) on every server restart/crash. |
| 2 | HIGH | `stop_job` 263-266 vs `_run_job` 183-191 | Status race: `stop_job` writes `CANCELLED`, but the still-blocked `wait()` thread later sees the SIGTERM exit code and **overwrites it with `FAILED`**. |
| 3 | MEDIUM | `stop_job` line 263 | SIGTERM only — no `wait(timeout=...)` and no SIGKILL escalation. A trainer stuck in a CUDA call never dies, yet the API reports success. |
| 4 | MEDIUM | `Popen` lines 155-162 | No `start_new_session=True` / `os.killpg` -> cannot kill the whole process tree. |
| 5 | MEDIUM | `launch` lines 231-257 | Unbounded concurrent jobs (no semaphore/queue). Two simultaneous launches will fight for the single GPU. |
| 6 | MEDIUM | `_build_merged_config` lines 53-82 | Mac epochs guard is applied **before** the base/recipe config is merged: `merged_config = {"epochs": 1}` then `deep_merge(seed_config, merged_config)` lets the guard override recipe epochs. Contradicts its own comment ("unless explicitly overridden") — only `job.overrides` can win. On a Mac, recipe-configured epochs silently become 1. |
| 7 | LOW | lines 155-163 | `Popen` is registered in `active_processes` after creation — small window where `stop_job` cannot see a running process. |
| 8 | LOW | lines 121, 171, 190, 199, 243, 265 | `datetime.utcnow()` is deprecated (Python 3.12+); cosmetic. |
| 9 | OK | lines 138-145 | `shell=False` list-form command -> no shell injection; `dataset_path`/config paths are server-generated or registry-validated. |
| 10 | OK | lines 154-164 | Log file held open for the job lifetime inside `with` — intentional, not a leak; `finally` cleanup (line 202) prevents registry leaks. |

---

## Top recommendations

1. Add a FastAPI shutdown hook (lifespan or `atexit`) that `terminate()`s every entry in `active_processes`.
2. Use `start_new_session=True` and kill via `os.killpg(os.getpgid(proc.pid), SIGTERM)` to take down the whole tree.
3. Escalate in `stop_job`: `terminate()` -> `wait(timeout=10)` -> `kill()`.
4. On startup, reconcile the DB: mark stale `RUNNING` jobs from a previous process as `FAILED`/`CANCELLED`.
5. Make `_run_job` respect terminal states: don't overwrite `CANCELLED` with `FAILED` (re-read status before writing).
6. Add a concurrency limit (semaphore of 1 for a single-GPU box).
7. Move the Mac epochs guard to **after** base-config merging, so it only applies when neither config nor overrides specify `epochs`.

---
---

# Path Construction & OS Portability Audit (backend/core)

Scope: `backend/core/config.py` (28 lines), `backend/core/model_manager.py` (75 lines).
Focus: string-concatenation paths, hardcoded OS separators, and logic that breaks on Windows or a different directory layout.

---

## Verdict: no string-concatenation path building

Both files are clean on the headline question:
- `config.py:10` — `workspace_root` uses `pathlib.Path(__file__).resolve().parents[2]`.
- `model_manager.py:17` — uses the pathlib `/` operator (`settings.workspace_root / "backend" / "models" / stage`), which is OS-independent.
- `model_manager.py:34, 50, 64` — use `os.path.join`, also OS-independent.
- No hardcoded `/` or `\\` filesystem separators anywhere. The only `/` literal (`model_manager.py:30`, `cache_key = f"{stage}/{name}"`) is a dictionary key, not a filesystem path — no OS impact.

---

## Flaws found

| # | Severity | Location | Flaw |
|---|---|---|---|
| 1 | MEDIUM | `config.py:17` `env_file=".env"` | Relative to the **current working directory**, not `workspace_root`. If the server is launched from anywhere except the repo root (e.g. `cd backend && uvicorn ...`, systemd `WorkingDirectory`, or the training worker's `cwd`), `.env` is silently not loaded and secrets/overrides vanish with no error. |
| 2 | MEDIUM | `config.py:10` `parents[2]` | Hardcodes the file's depth (`backend/core/config.py` -> 3 levels up). Moving `config.py` one level deeper/shallower silently shifts `workspace_root`, and every downstream path (models dir, SQLite DBs, log dirs) then points into a wrong tree **without any error**. No sanity check that the computed root is actually the repo root. |
| 3 | MEDIUM | `model_manager.py:53-65` + deploy symlinks | The model registry deploy flow creates **symlinks** in `backend/models/stageN/`. On Windows: (a) symlink creation requires admin or Developer Mode, and (b) with git `core.symlinks=false`, clones materialize symlinks as plain text files — those pass the `os.path.isfile()` filter (line 64), so `get_model` tries `YOLO(<text file>)` and fails with a cryptic ultralytics error instead of a clear "symlink unsupported" message. |
| 4 | LOW | `config.py:10` `.resolve()` | Follows symlinks. If the repo is deployed via a symlinked checkout, `workspace_root` resolves to the real target path, which can diverge from paths other components assume. Minor. |
| 5 | LOW | Windows clones generally | Deep artifact paths (`runs/segment/.../weights/best.pt` nested under long user dirs) can exceed Windows MAX_PATH (260) unless Long Paths are enabled — ultralytics file I/O would fail. Not a flaw in these two files, but a clone-location risk. |
| 6 | OK | `config.py:10` derivation | Because the root is derived from `__file__`, cloning to any directory (MacBook path, server `/home/lamacpp/Documents/car_defect_detection`) works — **no absolute paths** in either file. |

---

## Top recommendations

1. Anchor `.env` to the repo root: compute `ROOT = Path(__file__).resolve().parents[2]` and set `env_file=str(ROOT / ".env")` (or pass it via `Settings(_env_file=...)`).
2. Fail fast on a wrong `workspace_root`: assert `(workspace_root / "backend").is_dir()` at startup.
3. On Windows, either require Developer Mode for the deploy symlink flow or copy/promote real `.pt` files instead of symlinking; add an explicit check in `list_available_models` for symlinks that are not valid files.
4. If `config.py` ever moves, replace the magic `parents[2]` with an upward search for a repo marker (e.g. `AGENTS.md`/`.git`).
