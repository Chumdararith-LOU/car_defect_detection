# Workspace Report — Application React

Generated: 2026-08-16
Scope: frontend-only deep analysis (React / Vite / TanStack Start). Backend listed for context only.

---

## 1. Overview

This is the frontend of an **AI Exterior Defect Inspection** platform for automotive quality control. It is a multi-page SSR-capable React app built on **TanStack Start** (file-based routing + Nitro server), styled with **Tailwind CSS v4** and **shadcn/ui (new-york style)**. The app covers the full MLOps loop for a multi-stage YOLO26 detection pipeline:

- **Inspection** (`/`) — run a 3-stage defect detection pipeline on a vehicle image, visualize boxes/panels, filter & export results.
- **Review** (`/review`) — operator review queue for confirming / rejecting / reclassifying detections.
- **Datasets** (`/datasets`) — dataset versioning, leakage audit, splits, tiling, and a "review-to-dataset" flywheel builder.
- **Training** (`/training`) — launch and monitor YOLO training jobs.
- **Experiments** (`/experiments`) — compare training runs and metrics.
- **Settings** (`/settings`) — placeholder for backend URL / runtime config (Phase 7).
- **Host** (`/host`) — host profile / system info page.

The frontend talks to a separate FastAPI backend (`backend/`) over REST, base URL from `VITE_API_BASE` (default `http://localhost:8010`).

Repo root layout (non-generated):

```
AGENTS.md, plan.md, FRONTEND_REPORT.md   # docs / agent instructions
backend/                                 # FastAPI + YOLO backend (out of scope)
images/                                  # loose test/reference images (~19 files, 7.1 MB)
src/                                     # all frontend source
package.json, bun.lock, bunfig.toml      # Bun-managed deps
vite.config.ts, tsconfig.json            # build + TS config
components.json                          # shadcn/ui config (new-york, slate, lucide)
eslint.config.js, prettierrc, prettierignore
.env                                     # VITE_API_BASE (gitignored)
```

---

## 2. Tech Stack & Dependencies

### Frontend

| Layer | Tech |
|---|---|
| Language | TypeScript ^5.8.3 (strict, `noEmit`, ES2022, Bundler resolution) |
| Runtime / package mgr | Bun (`bun.lock`, `bunfig.toml`); scripts via `vite` |
| Build | Vite ^8.0.16, `@lovable.dev/vite-tanstack-config` ^2.7.1 |
| Framework | TanStack Start ^1.168.26 + TanStack Router ^1.170.16 |
| SSR server | Nitro 3.x beta (Cloudflare target by default), entry wrapped by `src/server.ts` |
| Data | @tanstack/react-query ^5.101.1 (router context only — no hooks used yet) |
| Styling | Tailwind CSS ^4.2.1 (`@tailwindcss/vite`), `tw-animate-css`, `tailwind-merge`, `class-variance-authority`, `clsx` |
| UI kit | shadcn/ui primitives over Radix UI (accordion, alert-dialog, aspect-ratio, avatar, checkbox, collapsible, context-menu, dialog, dropdown-menu, hover-card, label, menubar, navigation-menu, popover, progress, radio-group, scroll-area, select, separator, slider, slot, switch, tabs, toggle, toggle-group, tooltip) |
| Charts | recharts ^2.15.4 |
| Forms | react-hook-form ^7.71.2 + @hookform/resolvers + zod ^3.24.2 |
| Icons | lucide-react ^0.575.0 |
| Misc | sonner (toasts), vaul (drawer), cmdk (command), date-fns, react-day-picker, embla-carousel-react, input-otp, react-resizable-panels, vite-tsconfig-paths |
| Lint/format | ESLint ^9 (+ prettier, react-hooks, react-refresh, typescript-eslint) |

Scripts: `dev`, `build`, `build:dev`, `preview`, `lint`, `format`. No `typecheck` or test script.

### Backend (context only)

FastAPI 0.139 + uvicorn, Pydantic 2, ultralytics 8.4.115 (YOLO26), SAHI 0.12.4, shapely, numpy/pillow/opencv. Layout: `api/routes.py`, `core/model_manager.py`, `core/system_metrics.py`, `services/{stage1,stage2_direct,stage2_sahi,image_utils}.py`, `configs/sahi_production.yaml`, `models/{stage1,stage2,stage3}`.

---

## 3. Directory Tree

Excludes: `node_modules`, `__pycache__`, `.git`, `.venv`, lock files, model weights (summarized below), images/media, `.DS_Store`, `.idea/.vscode`.

```
Application React/
├── AGENTS.md
├── FRONTEND_REPORT.md
├── WORKSPACE_REPORT.md            # this file
├── plan.md
├── .env                           # VITE_API_BASE (gitignored)
├── .gitignore
├── bunfig.toml
├── components.json                # shadcn config
├── eslint.config.js
├── package.json
├── prettierignore                 # NOTE: should be .prettierignore
├── prettierrc                     # NOTE: should be .prettierrc
├── tsconfig.json
├── vite.config.ts
├── opencode.json
├── .tanstack/tmp/                 # TanStack dev cache
├── images/                        # 19 reference/test images, ~7.1 MB (media, not listed individually)
├── backend/                       # FastAPI backend (context only)
│   ├── BACKEND_REPORT.md
│   ├── Structure.md
│   ├── config.py
│   ├── main.py
│   ├── requirements.txt
│   ├── sahi_inference.py
│   ├── schemas.py
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes.py
│   ├── configs/
│   │   └── sahi_production.yaml
│   ├── core/
│   │   ├── __init__.py
│   │   ├── model_manager.py
│   │   └── system_metrics.py
│   ├── models/
│   │   ├── stage1/                # 2 .pt files, ~137 MB
│   │   ├── stage2/                # 8 .pt files, ~520 MB (incl. backup below)
│   │   │   └── _backup_20260806_120910/   # 2 .pt files, ~104 MB
│   │   └── stage3/                # 0 files (empty)
│   └── services/
│       ├── __init__.py
│       ├── image_utils.py
│       ├── stage1.py
│       ├── stage2_direct.py
│       └── stage2_sahi.py
└── src/
    ├── router.tsx
    ├── server.ts                  # SSR fetch wrapper (error capture + 500 page)
    ├── start.ts                   # TanStack Start instance + server middleware
    ├── styles.css                 # Tailwind v4 + shadcn theme tokens
    ├── routeTree.gen.ts           # AUTO-GENERATED by TanStack router plugin — do not edit
    ├── assets/
    │   └── demo-vehicle.jpg       # demo input image (media)
    ├── components/
    │   ├── Datasets/              # 21 files + index.ts
    │   │   ├── ClassDistributionBar.tsx
    │   │   ├── CreateDatasetDialog.tsx
    │   │   ├── DatasetDetailPanel.tsx
    │   │   ├── DatasetListView.tsx
    │   │   ├── DatasetPrepPanel.tsx
    │   │   ├── FileUploader.tsx
    │   │   ├── ImageGallery.tsx
    │   │   ├── ImageViewer.tsx
    │   │   ├── ImportDatasetDialog.tsx
    │   │   ├── ImportPanel.tsx
    │   │   ├── InspectionPicker.tsx
    │   │   ├── LeakageAuditPanel.tsx
    │   │   ├── MaskOverlay.tsx
    │   │   ├── NewDatasetDialog.tsx
    │   │   ├── ReclassifyDialog.tsx
    │   │   ├── ResplitDialog.tsx
    │   │   ├── ReviewToDatasetBuilder.tsx
    │   │   ├── SplitStructurePanel.tsx
    │   │   ├── TileDialog.tsx
    │   │   ├── ZipUploader.tsx
    │   │   ├── datasetUtils.ts
    │   │   └── index.ts
    │   ├── Experiments/
    │   │   ├── ExperimentDashboard.tsx
    │   │   ├── ExperimentList.tsx
    │   │   ├── RunComparisonTable.tsx
    │   │   └── index.ts
    │   ├── Inspection/
    │   │   ├── ControlSidebar.tsx
    │   │   ├── InspectionCanvas.tsx
    │   │   ├── StageStatus.tsx
    │   │   ├── SummaryCard.tsx
    │   │   ├── SystemMetricsPanel.tsx
    │   │   ├── export/
    │   │   │   ├── ExportReportButton.tsx
    │   │   │   ├── index.ts
    │   │   │   └── reportBuilder.ts
    │   │   └── gallery/
    │   │       ├── AnomalyCard.tsx
    │   │       ├── DefectCard.tsx
    │   │       ├── DefectGallery.tsx
    │   │       ├── ReviewFooter.tsx
    │   │       ├── SuppressedCard.tsx
    │   │       ├── cropStyle.ts
    │   │       └── index.ts
    │   ├── Training/
    │   │   ├── JobDetailPanel.tsx
    │   │   ├── JobListTable.tsx
    │   │   ├── LaunchTrainingDialog.tsx
    │   │   ├── TrainingDashboard.tsx
    │   │   └── index.ts
    │   └── ui/                    # 46 shadcn/ui primitives (see §4)
    ├── hooks/
    │   ├── use-mobile.tsx
    │   └── useInspection.ts
    ├── lib/
    │   ├── error-capture.ts
    │   ├── error-page.ts
    │   ├── lovable-error-reporting.ts
    │   ├── utils.ts
    │   └── inspection/
    │       ├── apiClient.ts
    │       ├── constants.ts
    │       ├── demoPayload.ts
    │       ├── experimentSchema.ts
    │       ├── mockPipeline.ts
    │       ├── prepSchema.ts
    │       ├── schema.ts
    │       └── trainingSchema.ts
    └── routes/
        ├── README.md              # file-routing conventions
        ├── __root.tsx             # app shell + nav + QueryClientProvider
        ├── index.tsx              # / (Inspection dashboard)
        ├── datasets.tsx
        ├── experiments.tsx
        ├── host.tsx
        ├── review.tsx
        ├── settings.tsx
        └── training.tsx
```

### Model weights summary (not listed individually)

| Folder | Files | Size |
|---|---|---|
| `backend/models/stage1` | 2 `.pt` | ~137 MB |
| `backend/models/stage2` | 8 `.pt` (incl. backup) | ~520 MB |
| `backend/models/stage2/_backup_20260806_120910` | 2 `.pt` | ~104 MB |
| `backend/models/stage3` | 0 | empty |

`backend/models` is gitignored. Total weight footprint on disk ≈ **657 MB**.

---

## 4. Frontend Breakdown

### `src/routes/` — TanStack Router file-based routing

| File | URL | Role |
|---|---|---|
| `__root.tsx` | — | App shell: `<html>/<body>`, `HeadContent`, `Scripts`, top nav, `QueryClientProvider`, `Outlet`, 404 component |
| `index.tsx` | `/` | Inspection dashboard (page-level component lives here, uses `useInspection`) |
| `review.tsx` | `/review` | Review queue UI (fully inline in the route file, ~390 lines) |
| `datasets.tsx` | `/datasets` | Datasets list/detail/builder view switcher |
| `training.tsx` | `/training` | Thin wrapper → `TrainingDashboard` |
| `experiments.tsx` | `/experiments` | Thin wrapper → `ExperimentDashboard` |
| `settings.tsx` | `/settings` | Static settings card (Phase 7 placeholder) |
| `host.tsx` | `/host` | Host profile display |
| `README.md` | — | Routing conventions doc |
| `routeTree.gen.ts` (in `src/`) | — | Auto-generated route tree — do not edit |

### `src/components/Inspection/`

| File | Responsibility |
|---|---|
| `ControlSidebar.tsx` | Left controls: model/stage selection, presets, confidence slider, run/reset actions |
| `InspectionCanvas.tsx` | Main image canvas with bbox/panel overlays & hover sync |
| `StageStatus.tsx` | Pipeline stage indicator (idle/prescreen/tiling/context/done/error) |
| `SummaryCard.tsx` | Per-inspection summary stats |
| `SystemMetricsPanel.tsx` | Backend CPU/GPU/memory metrics display |
| `export/ExportReportButton.tsx` | Download inspection report |
| `export/reportBuilder.ts` | Builds report JSON + filename |
| `export/index.ts` | Barrel |
| `gallery/DefectGallery.tsx` | Detection gallery container w/ tabs & filters |
| `gallery/DefectCard.tsx` | Single defect card w/ crop preview + hover |
| `gallery/AnomalyCard.tsx` | Unclassified anomaly card |
| `gallery/SuppressedCard.tsx` | Suppressed/low-conf detection card |
| `gallery/ReviewFooter.tsx` | Operator decision footer (confirm/reject/reclassify) |
| `gallery/cropStyle.ts` | bbox → CSS crop/box helpers |
| `gallery/index.ts` | Barrel |

### `src/components/Datasets/`

Dataset management feature: list/detail views, prep panel (import/resplit/tile/split structure), leakage audit, image gallery + viewer with mask overlays, review-to-dataset builder, and dialogs (create/new/import/reclassify/resplit/tile) plus uploaders (file/zip). `datasetUtils.ts` holds shared helpers; `index.ts` is the barrel.

### `src/components/Training/` & `src/components/Experiments/`

Training: job list table, job detail panel, launch dialog, dashboard. Experiments: experiment list, run comparison table, dashboard. Both have `index.ts` barrels.

### `src/components/ui/` — shadcn/ui primitives

**46 shadcn primitives — standard, unmodified** (accordion, alert, alert-dialog, aspect-ratio, avatar, badge, breadcrumb, button, calendar, card, carousel, chart, checkbox, collapsible, command, context-menu, dialog, drawer, dropdown-menu, form, hover-card, input, input-otp, label, menubar, navigation-menu, pagination, popover, progress, radio-group, resizable, scroll-area, select, separator, sheet, sidebar, skeleton, slider, sonner, switch, table, tabs, textarea, toggle, toggle-group, tooltip). Only `toggle-group.tsx` cross-imports another primitive (`toggleVariants`), which is standard shadcn behavior. No customization beyond defaults detected.

### `src/hooks/`

| File | Responsibility |
|---|---|
| `useInspection.ts` | Central inspection state machine (useReducer): image, payload, filters, stage; localStorage persistence; calls `runInspection` |
| `use-mobile.tsx` | `useIsMobile` media-query hook (used by `ui/sidebar.tsx`) |

### `src/lib/`

| File | Responsibility |
|---|---|
| `utils.ts` | `cn()` class merge helper |
| `error-capture.ts` | Global error capture for SSR boundary |
| `error-page.ts` | Renders 500 HTML page |
| `lovable-error-reporting.ts` | Reports errors to Lovable telemetry |
| `inspection/apiClient.ts` | All backend REST calls (`API_BASE` from `VITE_API_BASE`): models, inspection, review, datasets, prep, training, experiments, host |
| `inspection/schema.ts` | Core domain types: defect classes, panels, pipeline stages, payloads |
| `inspection/constants.ts` | `DEFECT_CLASSES`, `PANEL_LABELS`, color helpers |
| `inspection/prepSchema.ts` | Dataset import/resplit/tile request/response types |
| `inspection/trainingSchema.ts` | Training job types |
| `inspection/experimentSchema.ts` | Experiment/run types |
| `inspection/mockPipeline.ts` | Mock pipeline event emitter (dev fallback) |
| `inspection/demoPayload.ts` | `DEMO_PAYLOAD` / `CLEAN_PAYLOAD` fixtures |

### Entry points & server flow

- **`src/start.ts`** — creates the TanStack Start instance with a server-side request middleware that catches non-HTTP errors and returns the rendered 500 page.
- **`src/server.ts`** — the Nitro/server entry (wired via `tanstackStart.server.entry` in `vite.config.ts`). Wraps `@tanstack/react-start/server-entry`'s `fetch` with try/catch, consuming captured errors from `error-capture.ts` and returning `renderErrorPage()` on failure.
- **`src/router.tsx`** — `getRouter()` builds the router with the generated `routeTree` and a fresh `QueryClient` in context.
- **Vite dev flow**: `bun dev` → Vite dev server with the Lovable config preset (TanStack Start plugin, React, Tailwind, tsconfig paths, devtools). Nitro/server entry is only used for SSR/production builds (`bun build`).
- **`vite.config.ts`** — uses `@lovable.dev/vite-tanstack-config`'s `defineConfig`; only override is `tanstackStart.server.entry = "server"`.

---

## 5. Key Files & Entry Points

| Concern | File |
|---|---|
| HTML shell / layout | `src/routes/__root.tsx` |
| Router factory | `src/router.tsx` |
| Start instance / middleware | `src/start.ts` |
| SSR server entry | `src/server.ts` |
| Vite config | `vite.config.ts` |
| Theme / global CSS | `src/styles.css` |
| Backend API client | `src/lib/inspection/apiClient.ts` |
| Inspection state | `src/hooks/useInspection.ts` |
| Domain schema | `src/lib/inspection/schema.ts` |
| shadcn config | `components.json` |
| Env config | `.env` (`VITE_API_BASE`) |

---

## 6. Observations for Refactoring

### Dead / unused code
1. **`demoPayload.ts` & `mockPipeline.ts` appear unused.** `DEMO_PAYLOAD`, `CLEAN_PAYLOAD`, and `runMockPipeline` are only defined, never imported elsewhere (grep confirms no consumers). If the demo path was replaced by the real backend, delete both files or gate them behind an explicit dev flag.
2. **`CreateDatasetDialog` is dead.** It is imported in `datasets.tsx` (line 9) and exported from the barrel, but `showCreateDialog` state is never used to render it — only `NewDatasetDialog` renders. Likely superseded by `NewDatasetDialog`; remove one of them.
3. **`ImportDatasetDialog`** is exported from the barrel but never imported by any route — verify whether it's used inside another Datasets component or remove.
4. **Many shadcn primitives are unused** (calendar, carousel, chart, input-otp, menubar, navigation-menu, pagination, breadcrumb, context-menu, hover-card, resizable, aspect-ratio, avatar, collapsible, command, drawer, radio-group, accordion, alert-dialog, toggle, toggle-group, sidebar, form, etc. — no imports found outside `ui/`). `ui/sidebar.tsx` (and its `useIsMobile` dependency) also has no consumers. Consider pruning to reduce bundle surface.
5. **`backend/models/stage3/` is empty** and `stage2/_backup_20260806_120910/` holds ~104 MB of duplicate checkpoints — archive off-repo.

### Structure & consistency
6. **`review.tsx` is a 390-line monolith** with inline form/table logic — extract into `src/components/Review/*` to match the feature-folder pattern used by Inspection/Datasets/Training.
7. **Inconsistent quote style**: `settings.tsx` and `host.tsx` use single quotes + no semicolons while the rest of the codebase uses double quotes + semicolons. Also `prettierrc`/`prettierignore` are missing their leading dots (`.prettierrc`, `.prettierignore`), so Prettier likely ignores them — the `format` script may not behave as intended.
8. **Import path inconsistency**: `host.tsx` uses relative `../lib/inspection/apiClient` while everything else uses `@/lib/...`.
9. **`datasets.tsx` has redundant `loadDatasets`/`handleBackFromBuilder` duplication** and both `showCreateDialog` + `showNewDialog` state.

### Data layer
10. **React Query is installed and injected into router context but never used** (no `useQuery`/`useMutation` anywhere). All pages hand-roll `useState` + `useEffect` fetch loops with duplicated loading/error handling. Adopting React Query (or loaders via TanStack Router) would eliminate repeated boilerplate across review/datasets/training/experiments/host.
11. **No `typecheck` script** (`tsc --noEmit`) and no test setup — add `npm run typecheck` given `noEmit: true` in tsconfig.

### Naming
12. Package name is still the scaffold default `tanstack_start_ts`.
13. Two overlapping reports exist (`FRONTEND_REPORT.md`, this file) — consolidate documentation.
