# Integration Guide — Car Defect Inference API

**Audience:** Frontend engineers integrating with the inference API.
**Prerequisite:** the service is running and reachable (see [README.md](README.md)).

This guide covers everything a frontend developer needs to call the API, draw
results on a canvas, filter by panel, and process batch jobs.

---

## 1. Running the service (30-second start)

```bash
conda activate car_defect
cd /path/to/inference-api
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

OpenAPI docs at `http://localhost:8000/docs` — use the Swagger UI to try every
endpoint interactively.

---

## 2. Coordinate conventions (read this first)

Every coordinate in every response is **normalized to `[0, 1]`** relative to
the uploaded image's width and height.

| Field | Shape | Meaning |
|---|---|---|
| `bbox` | `[x1, y1, x2, y2]` | Top-left corner → bottom-right corner |
| `polygon` | `[[x, y], ...]` | Closed mask outline (first point ≠ last) |
| `imageDims.width / height` | `int` | Original image pixel dimensions |

To convert to pixel coordinates on a rendered `<canvas>` of size `W × H`:
```js
const px = coord => coord * W;
const py = coord => coord * H;
```

---

## 3. The `Defect` object, field by field

```json
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
```

| Field | What to show the operator |
|---|---|
| `class` | Defect type (one of the 7 canonical classes, or `defect_unknown`) |
| `confidence` | 0–1 score; color-code polygons by this value |
| `bbox` / `polygon` | Use `polygon` for tight overlays; `bbox` for quick bounding boxes |
| `panel` | Snake_case panel id (see panel-id mapping table in [API.md](API.md#panel-id-mapping)) |
| `iod` | Containment ratio: how much of the defect lies inside its assigned panel (0–1) |
| `dsi` | Damage Severity Index: fraction of the panel's area covered (0–1). `dsi < 0.001` is "light", `dsi ≥ 0.01` is "heavy" |
| `crop_url` | Relative URL; prepend your API base to fetch the close-up PNG |

---

## 4. Drawing overlays on an HTML canvas

```js
async function drawInspection(canvasEl, imageUrl, payload) {
  const ctx = canvasEl.getContext("2d");
  const img = new Image();
  img.src = imageUrl;
  await img.decode();
  canvasEl.width = img.width;
  canvasEl.height = img.height;
  ctx.drawImage(img, 0, 0);

  const W = img.width, H = img.height;

  // Panels (draw first, translucent blue)
  (payload.panels || []).forEach(p => {
    ctx.beginPath();
    p.polygon.forEach(([x, y], i) => {
      const method = i === 0 ? "moveTo" : "lineTo";
      ctx[method](x * W, y * H);
    });
    ctx.closePath();
    ctx.fillStyle = "rgba(33, 150, 243, 0.15)";
    ctx.fill();
    ctx.strokeStyle = "rgba(33, 150, 243, 0.6)";
    ctx.stroke();
  });

  // Defects (draw on top, colored by class)
  const colors = {
    corrosion: "rgba(244, 67, 54, 0.4)",
    scratch:   "rgba(255, 193, 7, 0.4)",
    dent:      "rgba(156, 39, 176, 0.4)",
    crack:     "rgba(0, 188, 212, 0.4)",
    glass_shatter: "rgba(233, 30, 99, 0.4)",
    broken_part:   "rgba(121, 85, 72, 0.4)",
    disjoint_part: "rgba(96, 125, 139, 0.4)",
    defect_unknown:"rgba(158, 158, 158, 0.4)",
  };
  payload.defects.forEach(d => {
    ctx.beginPath();
    d.polygon.forEach(([x, y], i) => {
      const method = i === 0 ? "moveTo" : "lineTo";
      ctx[method](x * W, y * H);
    });
    ctx.closePath();
    ctx.fillStyle = colors[d.class] || "rgba(0,0,0,0.4)";
    ctx.fill();
    ctx.strokeStyle = "red";
    ctx.lineWidth = 2;
    ctx.stroke();
  });
}
```

---

## 5. Showing the close-up crop

The `crop_url` field on each `Defect` is a relative path (e.g.
`/v1/crops/INSP_..._000.png`). Fetch it and render next to the polygon:

```js
async function showDefectCrop(baseUrl, defect, imgEl) {
  const url = `${baseUrl}${defect.crop_url}`;
  imgEl.src = url;
  await imgEl.decode();
}
```

This is the image the operator sees when they click a defect on the main
canvas — a padded, high-contrast close-up that makes micro-defects like
corrosion legible at display resolution.

---

## 6. Filtering by panel

The frontend often wants "defects on the hood only". Filter client-side:

```js
function defectsOnPanel(payload, panelId) {
  return payload.defects.filter(d => d.panel === panelId);
}
```

Panel ids are snake_case (e.g. `hood`, `front_door`, `rear_bumper`). Use
`GET /v1/taxonomy` to fetch the full list of 21 panel ids for your UI
dropdown.

---

## 7. The `inspection_status` pass/fail flag

```json
{ "inspection_status": "FAIL", "total_defects_found": 2, ... }
```

- `"FAIL"` — at least one defect was confirmed after Stage-4 suppression.
- `"PASS"` — no defects survived.

The operator-facing summary card keys off this field directly.

---

## 8. Handling `defect_unknown`

A detection can have `"class": "defect_unknown"`. This means the objectness
gate confirmed physical damage is present, but the class head could not
determine the type with sufficient confidence. **These are real defects.**

Show them to the operator with a grey polygon and a label like
*"Damage (type uncertain)"*. They appear under the `safety` and
`max_recall` presets only.

---

## 9. Suppressed detections and unclassified anomalies

The payload includes two lists that are **not** defects but may be useful for
debugging or operator transparency:

| List | What it contains |
|---|---|
| `suppressed_detections` | Detections Stage 4 removed (e.g. tire overlaps, non-car context) |
| `unclassified_anomalies` | Stage-1 saliency blobs that didn't match any defect |

For a production UI, **ignore both** and render only `defects`. Add a
"Show debug overlays" toggle if operators want to see them.

---

## 10. Synchronous single-image call (the common case)

**Python (`requests`):**
```python
import requests
with open("car.jpg", "rb") as f:
    r = requests.post(
        "http://localhost:8000/v1/inspect",
        files={"file": ("car.jpg", f, "image/jpeg")},
        data={"preset": "safety", "return_crops": "true"},
    )
print(r.json()["total_defects_found"])
print(r.json()["defects"][0])
```

**JavaScript (`fetch`):**
```js
const formData = new FormData();
formData.append("file", fileInput.files[0]);
formData.append("preset", "safety");
formData.append("return_crops", "true");

const res = await fetch("http://localhost:8000/v1/inspect", {
  method: "POST",
  body: formData,
});
const payload = await res.json();
```

**`curl`:**
```bash
curl -X POST http://localhost:8000/v1/inspect \
  -F "file=@car.jpg" \
  -F "preset=safety" \
  -F "return_crops=true"
```

---

## 11. Advanced: stage toggles and model combos

Pass a `spec` JSON string (form-encoded) to override any stage:

```json
{
  "preset": "safety",
  "stage1": { "enabled": true },
  "stage2": { "enabled": true, "models": ["baseline_m5"], "merge": "none" },
  "stage3": { "enabled": false },
  "stage4": { "enabled": false },
  "return_crops": true
}
```

This runs **only** the `baseline_m5` model without routing, skips panel
segmentation and context mapping, and still generates crop URLs. Useful for
A/B comparisons in the UI or for debugging.

`stage2.merge` options: `"none"` | `"union"` | `"per_class"`.
`stage2.models`: array of model names from `GET /v1/models`.

---

## 12. Asynchronous batch workflow

For multi-image processing (fleet audits), use the batch endpoints:

```python
# 1. Submit the batch — returns immediately with a job_id
files = [("files", (name, open(path, "rb"), "image/jpeg")) for name, path in items]
submit = requests.post("http://localhost:8000/v1/inspect/batch",
                       files=files, data={"preset": "safety"}).json()
job_id = submit["job_id"]
total  = submit["total"]

# 2. Poll until done
import time
while True:
    job = requests.get(f"http://localhost:8000/v1/jobs/{job_id}").json()
    if job["status"] == "done":
        break
    if job["status"] == "failed":
        raise RuntimeError(job["error"])
    print(f"progress: {job['completed']}/{total}")
    time.sleep(2)

# 3. Each result in `job["results"]` has the same shape as /v1/inspect,
#    plus a `source_filename` field so you can map back to uploads.
for r in job["results"]:
    print(r["source_filename"], "->", r["total_defects_found"], "defects")
```

Recent jobs are listable via `GET /v1/jobs?limit=20`.

---

## 13. Three operating presets — when to use which

| Preset | When | FPR | Recall |
|---|---|---|---|
| `balanced` | High-throughput screening; minimize false alarms | ~28% | ~86% |
| `safety` | **Default.** Recall-first; acceptable ~4 false alarms per suspect car | 46.7% | 94.3% |
| `max_recall` | Offline auditing; surface the faintest micro-defects | ~58% | ~95% |

If the operator is auditing a specific vehicle and wants to be absolutely
sure nothing is missed, switch to `max_recall`. For a conveyor-belt triage UI,
use `balanced`. The default `safety` works for almost every other case.

---

## 14. Common gotchas

1. **`broken_part`, not `broken_lamp`.** The API always returns the canonical
   `broken_part` class name. Do not match on `broken_lamp` in the frontend.

2. **Coordinates are always normalized.** Never multiply by the image
   dimensions returned by `imageDims` unless you are drawing on a canvas of
   exactly that size. If the UI renders the image at a different size, use
   the rendered size.

3. **`panel` is snake_case.** `front_door`, not `Front-door`. Use the mapping
   table in [API.md](API.md#panel-id-mapping) for display labels.

4. **Defects with `panel: "Unknown"`** are real defects that didn't fall
   inside any detected panel (e.g. on a trim piece or gap). Still show them.

5. **Tire / wheel detections are suppressed** by Stage 4 and never appear in
   `defects`. They appear in `suppressed_detections` with `reason: "tire"`.

6. **Crops are PNG** served via `GET /v1/crops/{filename}`. They are stored on
   disk under `storage/crops/` on the server; in a long-running production
   deployment, add a cron job or lifecycle policy to purge old crops.

7. **Batch jobs don't auto-expire.** Add a retention policy that deletes old
   `storage/jobs/{job_id}/` directories after N days.

---

## 15. Minimal React component sketch

```jsx
function DefectInspector({ baseUrl, imageFile }) {
  const [payload, setPayload] = useState(null);
  const [selectedDefect, setSelectedDefect] = useState(null);

  useEffect(() => {
    if (!imageFile) return;
    const fd = new FormData();
    fd.append("file", imageFile);
    fd.append("preset", "safety");
    fetch(`${baseUrl}/v1/inspect`, { method: "POST", body: fd })
      .then(r => r.json())
      .then(setPayload);
  }, [imageFile]);

  if (!payload) return <div>Inspecting...</div>;

  return (
    <div className="inspector">
      <canvas ref={el => el && drawInspection(el, URL.createObjectURL(imageFile), payload)} />
      <div className="summary">
        Status: <b>{payload.inspection_status}</b> — {payload.total_defects_found} defects
      </div>
      <ul className="defect-list">
        {payload.defects.map(d => (
          <li key={d.id} onClick={() => setSelectedDefect(d)}>
            {d.class} on {d.panel} (conf {d.confidence.toFixed(2)})
          </li>
        ))}
      </ul>
      {selectedDefect?.crop_url && (
        <img className="crop" src={`${baseUrl}${selectedDefect.crop_url}`} />
      )}
    </div>
  );
}
```

---

## 16. Where to go next

- **Endpoint reference:** [API.md](API.md) — full request/response schemas
- **Service overview:** [README.md](README.md) — install, run, project layout
- **Interactive docs:** `http://<host>:8000/docs` once the service is running

Questions or integration issues? File a ticket against the backend repo with
the `inspection_id` and the full JSON response — both are enough to reproduce
any issue server-side.
