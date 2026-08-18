# Frontend Analysis Report

**Project:** AI Exterior Defect Inspection Dashboard
**Location:** `/Users/macbook/Documents/ITC8/Internship/AI Farm/Project/Application React`
**Date:** 2026-08-12

---

## Overview

A single-page operator dashboard for a 3-stage AI vehicle damage inspection pipeline (pre-screen → tiled instance segmentation → component context mapping). The frontend uploads a vehicle image, streams pipeline stage events, renders detection overlays (bounding boxes + polygons) on an SVG canvas, and lets operators filter defects by panel, class, confidence, and damage severity index (DSI). It talks to a Python (FastAPI) backend in `backend/` at `http://localhost:8000`, with a built-in demo payload for offline use. The whole app is one route (`/`) composed from ~7 domain components plus shadcn/ui primitives.

---

## Tech Stack & Dependencies

| Category | Choice | Evidence |
|---|---|---|
| Framework | TanStack Start (SSR on Vite) | `@tanstack/react-start ^1.168.26`, `vite.config.ts` |
| Router | TanStack Router (file-based) | `routeTree.gen.ts`, `router.tsx`, `src/routes/` |
| Bundler | Vite 8 via `@lovable.dev/vite-tanstack-config` | `vite.config.ts`, nitro build target (Cloudflare) |
| Package manager | Bun | `bun.lock`, `bunfig.toml` |
| UI kit | shadcn/ui (new-york style, slate base, CSS variables) | `components.json`, `src/components/ui/` |
| Styling | Tailwind CSS v4 (CSS-first config, oklch tokens) | `src/styles.css`, `@tailwindcss/vite` |
| View | React 19 | `package.json` |
| Server state | TanStack Query (installed, wired into router context, unused for fetching) | `@tanstack/react-query ^5.101.1` |
| Client state | `useReducer` inside a custom hook (no Redux/Zustand) | `src/hooks/useInspection.ts` |
| Icons | lucide-react | throughout |
| Forms/validation | react-hook-form + zod (installed, unused) | `package.json` |
| Backend | FastAPI + SAHI/YOLO models (`backend/`) | `backend/main.py`, `api/routes.py` |

**Unused installed runtime deps** (candidate for cleanup): `recharts`, `react-resizable-panels`, `sonner`, `vaul`, `cmdk`, `date-fns`, `embla-carousel-react`, `input-otp`, `react-day-picker`, `@hookform/resolvers`. Most exist only to satisfy installed-but-unused shadcn primitives.

---

## Directory Tree

```
.
├── AGENTS.md                     # agent instructions (Lovable project guardrails)
├── bunfig.toml                   # Bun config
├── components.json               # shadcn/ui config (new-york, slate, CSS vars)
├── eslint.config.js              # ESLint flat config
├── opencode.json                 # opencode tool config
├── package.json                  # scripts: dev/build/preview/lint/format
├── plan.md                       # product/pipeline planning notes
├── prettierignore / prettierrc   # formatting config
├── tsconfig.json                 # TS config with @/* path alias
├── vite.config.ts                # Lovable TanStack Start config wrapper
│
├── backend/                      # Python FastAPI inference server (out of scope)
│   ├── main.py, config.py, schemas.py, sahi_inference.py
│   ├── api/routes.py             # /api/models, /api/inspect, /api/system/metrics
│   ├── core/, services/, configs/
│   └── models/stage1|stage2|stage3   # model weights
│
├── images/                       # test input photos (jpg/webp/jpeg, ~15 files)
│
└── src/
    ├── server.ts                 # SSR entry: error-recovering fetch wrapper
    ├── start.ts                  # TanStack Start instance + server error middleware
    ├── router.tsx                # router factory with QueryClient context
    ├── routeTree.gen.ts          # auto-generated route tree (do not edit)
    ├── styles.css                # Tailwind v4 theme: all design tokens (oklch)
    │
    ├── routes/
    │   ├── __root.tsx            # root route: head/meta, scripts, error boundary, QueryClientProvider
    │   ├── index.tsx             # "/" dashboard page (the entire app)
    │   └── README.md
    │
    ├── components/
    │   ├── Inspection/           # domain components (7 files)
    │   │   ├── ControlSidebar.tsx, DefectCard.tsx, DefectGallery.tsx,
    │   │   ├── InspectionCanvas.tsx, StageStatus.tsx, SummaryCard.tsx,
    │   │   └── SystemMetricsPanel.tsx
    │   └── ui/                   # 47 shadcn/ui primitives (13 actually used)
    │
    ├── hooks/
    │   ├── useInspection.ts      # core state machine (reducer) for the inspection flow
    │   └── use-mobile.tsx        # shadcn sidebar helper (unused by app code)
    │
    ├── lib/
    │   ├── utils.ts              # cn() (clsx + tailwind-merge)
    │   ├── error-capture.ts      # out-of-band server error capture
    │   ├── error-page.ts         # static HTML 500 page
    │   ├── lovable-error-reporting.ts  # Lovable telemetry bridge
    │   └── inspection/           # domain layer
    │       ├── apiClient.ts      # fetch wrapper for FastAPI backend
    │       ├── mockPipeline.ts   # staged pipeline orchestrator (events + API call)
    │       ├── demoPayload.ts    # offline demo result (panels + defects)
    │       ├── constants.ts      # defect classes, panel labels, colors
    │       └── schema.ts         # TypeScript domain types
    │
    └── assets/
        └── demo-vehicle.jpg      # single bundled demo image (used by routes/index.tsx)
```

---

## Folder-by-Folder Breakdown

| Folder | Purpose |
|---|---|
| `src/routes/` | TanStack Router file-based routes. Only two: root layout and the single dashboard page. |
| `src/components/Inspection/` | Domain-specific inspection UI: controls, canvas overlay, defect list, summaries, live metrics. |
| `src/components/ui/` | shadcn/ui primitives (Radix-based). Installed wholesale; ~72% unused. |
| `src/hooks/` | Custom hooks. `useInspection` owns all app state; `use-mobile` is shadcn boilerplate. |
| `src/lib/inspection/` | Domain logic: API client, pipeline orchestration, demo data, types, constants. Cleanly separated from UI. |
| `src/lib/` | Shared utilities + SSR error-handling plumbing (Lovable/Start scaffolding). |
| `src/assets/` | One static demo image. |
| `backend/` | Python FastAPI server with 3 model stages (not frontend, but the API contract source). |
| `images/` | Loose test photos for manual API testing; not referenced by frontend code. |

---

## Key Files & Entry Points

### Entry / boot chain
- `src/server.ts` — SSR fetch entry. Wraps TanStack Start's server entry, recovers swallowed errors via `error-capture.ts`, renders `error-page.ts` on 500.
- `src/start.ts` — `createStart` instance with a server request middleware that converts unhandled errors to the static 500 page.
- `src/router.tsx` — `getRouter()` factory; creates a fresh `QueryClient` per router and injects it into route context.
- `src/routeTree.gen.ts` — auto-generated by router plugin; consumed by `router.tsx`.

### Routes
- `src/routes/__root.tsx` — root layout: `<HeadContent>` (meta/fonts), `<Scripts>`, React error boundary reporting to Lovable, `QueryClientProvider`, `<Outlet>`.
- `src/routes/index.tsx` — the dashboard. Calls `useInspection`, lays out `ControlSidebar` + `InspectionCanvas` + `DefectGallery` + `SummaryCard`; loads `demo-vehicle.jpg` as the default image.

### State & data flow
- `src/hooks/useInspection.ts` — **the state core**. `useReducer` managing: image, pipeline stage, status message, payload, filters (panels/classes/minConfidence/minDsi), view stage. Exposes `setImage/run/reset/setFilters/setViewStage` + memoized `filteredDefects`.
- `src/lib/inspection/mockPipeline.ts` — orchestrator named "mock" but actually calls the real API (`runInspection`); emits staged progress events (`prescreen → tiling → context → done`) with artificial delays, supports `forceClean` simulation.
- `src/lib/inspection/apiClient.ts` — fetch layer: `fetchModels()`, `runInspection()` (FormData POST), `fetchSystemMetrics()`; hardcoded `API_BASE = http://localhost:8000`.
- `src/lib/inspection/demoPayload.ts` — hand-tuned demo result (panel polygons, defects) for the bundled demo image.
- `src/lib/inspection/schema.ts` / `constants.ts` — domain types (`Defect`, `Panel`, `InspectionPayload`, `PipelineStage`, `ViewStage`) and label/color maps.

### Domain components
- `ControlSidebar.tsx` — image upload (drag-drop), model selection, stage-2 params, run/reset/export buttons, filter sliders, embeds `StageStatus` + `SystemMetricsPanel`.
- `InspectionCanvas.tsx` — SVG overlay layer over the image: panel polygons, defect bboxes/polygons, hover highlighting, per-stage visibility rules.
- `DefectGallery.tsx` / `DefectCard.tsx` — grid of defect cards with cropped previews (`object-position` from bbox), hover sync with canvas.
- `StageStatus.tsx` — 3-step pipeline progress indicator.
- `SummaryCard.tsx` — PASS/FAIL verdict + counts.
- `SystemMetricsPanel.tsx` — polls `/api/system/metrics` (GPU/CPU/RAM) on an interval.

---

## Design System & UI Analysis

### Design tokens (`src/styles.css`, Tailwind v4 CSS-first)
- **Color model:** all values in `oklch`. Standard shadcn semantic set (background/foreground/card/popover/primary/secondary/muted/accent/destructive/border/input/ring, chart-1..5, sidebar-*) **plus domain extensions**:
  - `--defect-*` (8 colors: scratch, anomaly, dent, crack, glass_shatter, broken_lamp, corrosion, disjoint_part) — referenced via `classColor()` and `DEFECT_CLASSES` in `constants.ts`.
  - `--status-pass` / `--status-fail` mapped to `--color-status-pass/fail` utilities.
- **Dark mode:** full `.dark` block defined; toggle implemented via `@custom-variant dark (&:is(.dark *))`. Note: no visible theme toggle in app code — dark tokens exist but light is the only applied mode.
- **Radii:** `--radius: 0.625rem` base with sm→4xl calc scale. Components mostly use small radii (`rounded-sm`), consistent with the industrial/mono aesthetic.
- **Typography:** `--font-display: "Chakra Petch"` (body default), `--font-mono: "JetBrains Mono"`. Heavy use of `font-mono text-[10px] uppercase tracking-widest` for labels — consistent technical-instrument look.
- **Spacing/shadows:** default Tailwind scale; no custom shadow tokens (components rely on borders rather than shadows — consistent).
- **No tailwind.config file** — v4 CSS-first via `@theme inline`, sourced with `@source "../src"`.

### shadcn/ui setup (`components.json`)
Style `new-york`, base color `slate`, `cssVariables: true`, icon library `lucide`, aliases `@/components|ui|lib|hooks` — all honored in code.

### Primitive usage (47 installed, 13 used)
**Used:** button (×6 imports), badge (×2), separator (×2), tooltip (×2), dialog, input, label, scroll-area, select, sheet, skeleton, slider, toggle.
**Installed-but-unused (34):** accordion, alert-dialog, alert, aspect-ratio, avatar, breadcrumb, calendar, card, carousel, chart, checkbox, collapsible, command, context-menu, dropdown-menu, form, hover-card, input-otp, menubar, navigation-menu, pagination, popover, progress, radio-group, resizable, sidebar, sonner, switch, table, tabs, textarea, toggle-group, drawer, toggle-group. These drag in unused deps (recharts, embla, cmdk, vaul, sonner, react-day-picker, input-otp, react-resizable-panels).

### Inspection component consistency review
- **Styling approach:** uniformly Tailwind utility classes + `cn()` + design-token colors; no inline styles or custom CSS beyond tokens. Very consistent aesthetic (mono uppercase micro-labels, thin borders, `rounded-sm`).
- **Composition:** components reuse ui primitives where sensible (Button, Select, Slider, Badge, ScrollArea, Tooltip, Separator). However several components hand-roll card-like surfaces (`rounded-sm border border-border bg-card p-4`) instead of the installed `Card` primitive — duplicated panel-chrome markup in `SummaryCard`, `SystemMetricsPanel`, `ControlSidebar` sections.
- **Props/naming:** consistent — local `interface Props`, `onHover(id | null)` pattern shared by gallery/canvas/card; data typed from `schema.ts`. Good.
- **Layout/responsive:** dashboard is a fixed desktop-oriented grid; `DefectGallery` has `sm:grid-cols-2` but the main 3-column layout has no real mobile breakpoints — the sidebar/canvas arrangement will be cramped on small screens.
- **Accessibility gaps:**
  - Canvas overlays are pure SVG with hover-only interaction — no keyboard focus, no `aria-label`/`role` on defect shapes.
  - Stage status & PASS/FAIL conveyed partly by color/icon only (icons do exist, but verify text alternatives for status badges).
  - Drag-drop upload zone: verify it is reachable/activatable by keyboard (hidden `<input type="file">` pattern).
  - Polling metrics panel updates without `aria-live`.
- **Demo asset:** `src/assets/demo-vehicle.jpg` is imported only in `src/routes/index.tsx` as the default image; `demoPayload.ts` polygons are hand-tuned to that exact image.

### Inconsistent patterns flagged
- `ControlSidebar` builds custom filter checkboxes/toggles from raw elements while shadcn `Checkbox`/`Switch` are installed.
- Card chrome duplicated instead of using `Card`/extracting a `Panel` wrapper.
- TanStack Query is wired into router context but all fetching is manual `fetch` + `useEffect` polling (`SystemMetricsPanel`) — two competing data-fetching paradigms.

---

## Observations for Refactoring

1. **`ControlSidebar.tsx` is 574 lines** — mixes upload logic, model fetching, filter state, export, and metrics. Split into `ImageUploadZone`, `ModelSettings`, `FilterPanel`, `ExportButton` subcomponents; move fetch/export logic into the hook or lib.
2. **`mockPipeline.ts` is misnamed** — it performs the real API call with staged UX events. Rename to `pipeline.ts` / `runPipeline` to avoid confusion; keep `forceClean` demo branch explicit.
3. **Hardcoded `API_BASE = "http://localhost:8000"`** — move to `import.meta.env.VITE_API_BASE` (the Lovable config already injects `VITE_*` env).
4. **Adopt TanStack Query** for `fetchModels` / `fetchSystemMetrics` (already installed and in router context) instead of manual `useEffect` polling; gives caching, retry, and stale-time control.
5. **Delete or prune unused shadcn primitives** (34 files) and their deps (recharts, cmdk, vaul, sonner, embla, react-day-picker, input-otp, react-resizable-panels, date-fns, @hookform/resolvers if forms stay unused) — significant bundle and maintenance reduction.
6. **Extract a shared `PanelSection`/`Card` wrapper** for the repeated `rounded-sm border bg-card p-4 + mono uppercase label` pattern.
7. **Add responsive handling** for the main dashboard grid (collapsible sidebar or stacked layout below `lg`).
8. **Accessibility pass:** keyboard-focusable defect list ↔ canvas sync, `aria-live` for pipeline stage messages and metrics, labels for sliders/filters.
9. **`use-mobile.tsx`** is unused boilerplate — remove.
10. **`images/` folder** (root) contains only manual test inputs — consider `.gitignore`-ing or moving to `backend/test_images` to keep the frontend repo clean; `src/components/.DS_Store` and root `.DS_Store` should be git-ignored/removed.
11. **Schema drift risk:** `schema.ts` types are hand-maintained duplicates of `backend/schemas.py`; consider generating TS types from the FastAPI OpenAPI schema.
