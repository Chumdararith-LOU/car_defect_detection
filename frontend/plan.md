# Multi-Stage Defect Inspection Dashboard (React)

A React/TanStack Start equivalent of the proposed Streamlit UI. All model outputs are mocked via a typed fixture that matches the JSON payload schema described in the proposal, so the UI is production-shaped and ready to wire to a real inference endpoint later.

## Scope

- Front-end only. No model runtime, no Cloud, no video.
- Single route: `/` (inspector dashboard).
- Static high-res image upload (or a bundled demo vehicle image) drives the flow.
- Pipeline is simulated with staged timers to demonstrate: Stage 1 pre-screen → Stage 2 tiling detect → Stage 3 component/context mapping.

## Layout (three zones, matches proposal)

```text
┌──────────────┬───────────────────────────────────────┬──────────────────────┐
│ Zone A       │ Zone B                                │ Zone C               │
│ Sidebar      │ Main canvas                           │ Defect gallery +     │
│ (controls +  │ (image + polygon overlays +           │ diagnostics +        │
│  filters)    │  panel boundaries + legend)           │ master summary       │
└──────────────┴───────────────────────────────────────┴──────────────────────┘
```

Responsive: 3-col on `xl:`, stacks to 1-col on mobile.

### Zone A — Control Sidebar
- Drag-and-drop image uploader (client-side `URL.createObjectURL`, no persistence).
- "Run Inspection" primary button → kicks off staged pipeline simulation.
- Stage status list: Pre-Screen / Tiling Detect / Context Mapping with pending → active → done states.
- Filters:
  - Panel multi-select (Hood, Roof, Doors L/R, Fenders, Quarter-panel, Bumper, Glass…).
  - Defect class multi-select (scratch, dent, crack, chip, discoloration).
  - Min confidence slider.
  - Min DSI slider.
- "Reset" and "Export JSON" (downloads current inspection payload).

### Zone B — Main Canvas
- Renders uploaded image in an aspect-preserving container.
- SVG overlay layer:
  - Panel polygons (stroke only, subdued color per panel, legend key).
  - Defect polygons (filled + stroked, color per defect class).
  - Hover a defect → highlights matching gallery card; click → scrolls gallery to it.
  - Filters in Zone A dim/hide non-matching overlays.
- Top-right overlay chip: Pre-screen verdict (PASS ✓ green / ACTIVE ROUTE amber).
- Legend (panels + defect classes) below canvas.

### Zone C — Gallery & Reporting
- Master Inspection Summary card at top:
  - Final status pill (PASS / FAIL) computed from defect count + DSI thresholds.
  - Total defects, detected vehicle color, timestamp, image dims.
- Auto-cropped defect gallery (grid of cards). Each card shows:
  - Cropped image (CSS `object-position` + scaling on the source image using the defect bbox — no server crop needed).
  - Defect class + confidence %.
  - Assigned panel.
  - Containment Ratio (IoD).
  - Damage Severity Index (DSI %).
  - Bbox coords (collapsible).
- Empty state when pre-screen returns PASS.

## Technical details

- Route: `src/routes/index.tsx` replaces the placeholder.
- Components under `src/components/inspection/`:
  - `ControlSidebar.tsx`
  - `InspectionCanvas.tsx` (image + SVG overlay)
  - `DefectGallery.tsx`, `DefectCard.tsx`
  - `SummaryCard.tsx`
  - `StageStatus.tsx`
  - `Legend.tsx`
- State: single `useReducer` in `src/hooks/useInspection.ts` holding `{ imageUrl, stage, payload, filters }`.
- Types + mock fixture in `src/lib/inspection/`:
  - `schema.ts` — `InspectionPayload`, `Defect`, `Panel`, `PreScreenResult` matching the proposal's JSON schema (class, confidence, panel, bbox, polygon, IoD, DSI, vehicle color, status).
  - `mockPipeline.ts` — `runMockPipeline(imageUrl)` returns a `Promise` that resolves stage-by-stage with `setTimeout`, emitting events via a callback so the sidebar can animate status.
  - `demoPayload.ts` — one realistic payload with ~6 defects across 3 panels, tuned to look right over the bundled demo image.
- Bundled demo vehicle image generated via `imagegen` (side-view sedan, studio lighting) so the app is usable without an upload.
- Styling: existing shadcn tokens + Tailwind v4. Introduce semantic tokens for defect classes and pass/fail states in `src/styles.css` (`--defect-scratch`, `--defect-dent`, `--defect-crack`, `--defect-chip`, `--status-pass`, `--status-fail`) — no hardcoded hex in components.
- SEO: route `head()` on `/` with real title/description ("AI Exterior Defect Inspection Dashboard"), og/twitter tags. Root `__root.tsx` metadata also updated away from "Lovable App" defaults.
- shadcn components used: `button`, `card`, `badge`, `slider`, `select`, `separator`, `scroll-area`, `progress`, `tooltip` (install any missing via existing setup).

## Out of scope (called out explicitly)
- Real model inference, Python/Streamlit, tiling algorithm, actual segmentation.
- Persistence, auth, multi-inspection history (can be added later with Lovable Cloud).
- Video streams, camera capture.

## Deliverable checklist
- Upload → run → PASS path works end-to-end with a clean image.
- Upload → run → FAIL path works with the demo image, showing overlays, gallery, filters, and summary.
- Filters live-update both canvas overlays and gallery.
- Export JSON downloads the current payload.
- Typecheck + build pass; no placeholder content remains on `/`.
