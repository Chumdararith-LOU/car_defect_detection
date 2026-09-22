# Car Defect Inference API

Production inference backend for automated car exterior defect detection. This
service exposes a REST API that runs a multi-stage deep-learning pipeline on
vehicle images and returns structured, panel-specific defect reports.

It is built to be consumed by a separate frontend application: upload an image
(or a batch of images), and receive defects with class, confidence, mask
polygon, assigned body panel, containment (IoD), damage severity (DSI), and a
crop URL for close-up display.

## What it does

The pipeline coordinates four stages, each individually toggleable:

| Stage | Model(s) | Purpose |
|---|---|---|
| 1 | `sod_champion` | Salient-object pre-screen (fast anomaly gate) |
| 2 | `objectness_branch_new`, `baseline_m5` (+ optional `surgical_early`, `model_4`) | Multi-class defect segmentation via SAHI tiling |
| 3 | `panel_champion` | Body-panel segmentation (21 panel classes) |
| 4 | (geometry only) | Panel assignment (IoD), severity (DSI), tire / car-context suppression |

Stage 2 ships three operating presets — `balanced`, `safety` (default),
`max_recall` — plus a `specialist` full-routing mode. Per-class multi-model
routing assigns each defect class to its best specialist model. Any stage can
be disabled, and Stage 2 can run arbitrary model combinations or a single
individual model via the `PipelineSpec`.

The seven defect classes are: `dent`, `scratch`, `crack`, `glass_shatter`,
`broken_part`, `corrosion`, `disjoint_part`. (`broken_part` is canonical; a
legacy `broken_lamp` label is normalized to `broken_part` internally.)

## Quick start

```bash
# 1. Create / activate the environment
conda activate car_defect

# 2. Install dependencies
pip install -r requirements.txt

# 3. Ensure model weights are present (see "Models" below)

# 4. Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

Interactive API docs are then available at `http://localhost:8000/docs`
(Swagger UI) and `http://localhost:8000/redoc`.

A minimal synchronous inspection:

```bash
curl -X POST http://localhost:8000/v1/inspect \
  -F "file=@/path/to/car.jpg" \
  -F "preset=safety"
```

## API

See [API.md](API.md) for the full endpoint reference (requests, responses,
status codes) and [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) for
frontend-oriented integration examples and the response schema.

## Project layout

```
inference-api/
├── app/
│   ├── main.py                 # FastAPI app, CORS, startup model preload
│   ├── config.py               # settings (paths, device, defaults)
│   ├── api/                    # HTTP endpoints (health, meta, inspect, batch, crops)
│   ├── pipeline/               # stage1..stage4, crops, orchestrator
│   ├── core/                   # device, image, model_registry, custom_head, job_queue
│   └── schemas/                # Pydantic request/response models
├── configs/production.yaml     # SAHI, NMS, routing, gating, presets
├── models/                     # model weights (Git LFS) + manifest.json
├── storage/                    # runtime artifacts (crops, jobs) — gitignored
├── scripts/                    # copy_models.py, download_models.py, verify_*.py
└── tests/
```

## Models

Weights live in `models/{stage1,stage2,stage3}/` and are tracked with Git LFS.
`models/manifest.json` is the registry (name, stage, role, sha256). If the
weights are not present after cloning, run:

```bash
python scripts/download_models.py
```

Required models are preloaded at startup: `sod_champion`,
`objectness_branch_new`, `baseline_m5`, `panel_champion`.

## Configuration

Most behaviour is driven by `configs/production.yaml` (tile size, overlap,
mask-IoS NMS threshold, two-tier gating, per-preset class rules, and routing
strategy). Service-level settings (device, paths, CORS origins, worker count)
come from `app/config.py` and can be overridden via environment variables
prefixed `INFERENCE_API_` or a local `.env` file.

## License / Ownership

Internal use — AI Farm Robotics / Institute of Technology of Cambodia.
