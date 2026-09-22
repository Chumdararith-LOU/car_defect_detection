# Car Defect Inference API — Endpoint Reference

**Version:** 1.0.0
**Base URL:** `http://<host>:8000/v1`
**Auth:** none (internal service)

Requests and responses are JSON unless noted. Interactive docs are available at
`GET /docs` (Swagger UI) and `GET /redoc`.

## Conventions

- **Coordinates** are normalized to `[0, 1]` relative to image width/height.
  `bbox` is `[x1, y1, x2, y2]`. `polygon` is a list of `[x, y]` points.
- **Defect classes:** `dent`, `scratch`, `crack`, `glass_shatter`, `broken_part`,
  `corrosion`, `disjoint_part`. A detection that clears the objectness gate but
  falls below class confidence is labeled `defect_unknown`.
- **Panel ids** (the defect `panel` field) are snake_case, e.g. `hood`,
  `front_door`, or `Unknown`. See [Panel id mapping](#panel-id-mapping).
- **Operating presets:** `balanced`, `safety` (default), `max_recall`, `specialist`.

---

## Core response schema: `InspectionPayload`

Returned by `POST /v1/inspect` and (per image) inside batch job results.

| Field | Type | Notes |
|---|---|---|
| `inspection_id` | string | Unique id, `INSP_<timestamp>_<hex>` |
| `timestamp` | string | ISO-8601 UTC |
| `vehicle_color_detected` | string | Currently always `"Unknown"` |
| `total_defects_found` | integer | Count of `defects` |
| `inspection_status` | string | `"FAIL"` if any defects, else `"PASS"` |
| `imageDims` | object \| null | `{ "width": int, "height": int }` |
| `preScreen` | object \| null | Stage 1 result (present if stage1 ran) |
| `panels` | array \| null | Panel polygons (present if stage3 ran) |
| `defects` | array | List of `Defect` objects |
| `unclassified_anomalies` | array | Stage-1 rescued blobs (unclassified) |
| `suppressed_detections` | array | Detections removed by Stage 4 |
| `stage1_blobs` | array | Raw Stage-1 saliency blobs |
| `disabled_stages` | array | Stages skipped for this run |
| `inference_ms` | number | Total wall-clock inference time |

### `Defect` object

| Field | Type | Notes |
|---|---|---|
| `id` | string | `<inspection_id>_S2_<index>` |
| `class` | string | Defect class (see Conventions) |
| `confidence` | number | 0–1 |
| `bbox` | array | `[x1, y1, x2, y2]` normalized |
| `polygon` | array | `[[x, y], ...]` normalized mask outline |
| `panel` | string | Snake_case panel id or `"Unknown"` |
| `iod` | number | Intersection-over-Defect containment, 0–1 |
| `dsi` | number \| null | Damage Severity Index (panel area fraction) |
| `crop_url` | string \| null | `GET` this to fetch the close-up image |

### `Panel` object

| Field | Type | Notes |
|---|---|---|
| `id` | string | Panel index within this image |
| `label` | string | Display label, e.g. `"Hood"`, `"Front-door"` |
| `polygon` | array | `[[x, y], ...]` normalized |

---

## GET /v1/health

Liveness + readiness probe.

**Response `200`**
```json
{
  "status": "ok",
  "app": "car-defect-inference-api",
  "version": "1.0.0",
  "device": "mps",
  "uptime_seconds": 123.4
}
```

## GET /v1/version

**Response `200`**
```json
{ "app": "car-defect-inference-api", "version": "1.0.0" }
```

## GET /v1/models

Lists all models in the registry with load status.

**Response `200`**
```json
{
  "models": [
    {
      "name": "objectness_branch_new",
      "stage": "stage2",
      "role": "Corrosion / disjoint_part specialist with objectness branch",
      "required": true,
      "on_disk": true,
      "loaded": true
    }
  ]
}
```

## GET /v1/presets

Returns the operating presets and their routing strategies from
`configs/production.yaml`.

**Response `200`**
```json
{
  "presets": {
    "safety": {
      "class_rules": { "corrosion": { "conf": 0.10, "min_area": 30 } },
      "two_tier_gating": { "obj_threshold": 0.20, "cls_threshold": 0.25 }
    }
  },
  "routing_strategy": {
    "safety": {
      "models": ["objectness_branch_new", "baseline_m5"],
      "merge": "per_class",
      "class_routing": { "corrosion": "objectness_branch_new" }
    }
  }
}
```

## GET /v1/taxonomy

**Response `200`**
```json
{
  "defect_classes": ["dent","scratch","crack","glass_shatter","broken_part","corrosion","disjoint_part"],
  "panel_classes": { "0": "Quarter-panel", "13": "Hood", "20": "Roof" }
}
```
(`panel_classes` contains all 21 panel classes.)

---

## POST /v1/inspect

Run the full pipeline on **one** image, synchronously. Returns the complete
`InspectionPayload`. Blocks until inference finishes (typically a few seconds).

**Request:** `multipart/form-data`

| Field | Type | Required | Default | Notes |
|---|---|---|---|---|
| `file` | file | yes | — | The vehicle image |
| `preset` | string | no | `safety` | Operating preset |
| `spec` | string (JSON) | no | — | Full `PipelineSpec` JSON; overrides everything if given |
| `return_crops` | boolean | no | `true` | Generate per-defect crop images |
| `device` | string | no | `auto` | `auto` \| `cuda` \| `mps` \| `cpu` |

### The `spec` object (optional, advanced)

Pass `spec` as a JSON string to toggle stages and control Stage-2 model
combinations. Omitting `spec` runs all stages with the chosen `preset`.

```json
{
  "preset": "safety",
  "stage1": { "enabled": true },
  "stage2": { "enabled": true, "models": ["objectness_branch_new", "baseline_m5"], "merge": "per_class" },
  "stage3": { "enabled": true },
  "stage4": { "enabled": true },
  "return_crops": true,
  "device": "auto"
}
```

- `stage2.models`: list of model names to run (overrides the preset's routing).
- `stage2.merge`: `"none"` | `"union"` | `"per_class"`.
- `stage2.class_routing`: optional `{ "class": "model_name" }` map.
- To run a **single model**, set `stage2.models` to one name and `merge` to `"none"`.

**Example request**
```bash
curl -X POST http://localhost:8000/v1/inspect \
  -F "file=@car.jpg" \
  -F "preset=safety"
```

**Response `200`** — an `InspectionPayload` (see schema above):
```json
{
  "inspection_id": "INSP_20260922140000_a1b2c3",
  "timestamp": "2026-09-22T14:00:02+00:00",
  "vehicle_color_detected": "Unknown",
  "total_defects_found": 1,
  "inspection_status": "FAIL",
  "imageDims": { "width": 1920, "height": 1080 },
  "preScreen": { "anomalyDetected": true, "score": 0.0012, "latencyMs": 45.2 },
  "panels": [ { "id": "0", "label": "Hood", "polygon": [[0.1,0.1],[0.6,0.1],[0.6,0.5],[0.1,0.5]] } ],
  "defects": [
    {
      "id": "INSP_20260922140000_a1b2c3_S2_000",
      "class": "corrosion",
      "confidence": 0.62,
      "bbox": [0.30, 0.20, 0.34, 0.24],
      "polygon": [[0.30,0.20],[0.34,0.20],[0.34,0.24],[0.30,0.24]],
      "panel": "hood",
      "iod": 0.985,
      "dsi": 0.0042,
      "crop_url": "/v1/crops/INSP_20260922140000_a1b2c3_000.png"
    }
  ],
  "unclassified_anomalies": [],
  "suppressed_detections": [],
  "stage1_blobs": [],
  "disabled_stages": [],
  "inference_ms": 2450.5
}
```

**Errors:** `400` (undecodable image), `422` (invalid `spec`), `500` (pipeline failure).
