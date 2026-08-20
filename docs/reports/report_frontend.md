# Frontend API Client Audit Report

File analyzed: `frontend/src/lib/inspection/apiClient.ts` (991 lines)

## 1. `any` / Untyped Response Usage

| Location | Issue |
|---|---|
| apiClient.ts:383 | `BatchSummary.settings: Record<string, any>` |
| apiClient.ts:400 | `createBatch(..., settings?: Record<string, any>)` |
| apiClient.ts:505 | `createNewDataset` returns `Promise<unknown>` (untyped response) |
| apiClient.ts:375 & :437 | `BatchSummary` interface declared **twice** — TypeScript silently merges declarations; the second lacks `settings`, masking intent |

No fetch call uses `Promise<any>` directly, but the items above are the only unconstrained types in the file.

## 2. Weak Error Handling (plain `throw`, backend `detail` lost, no `.json()` guard)

These functions throw a generic `Error` on `!res.ok` and never attempt to read the backend's `detail` field:

- `fetchModels` :90
- `runInspection` :96 — generic `API Error: ${statusText}`
- `fetchSystemDevices` :151
- `fetchSystemMetrics` :157
- `fetchHostProfile` :216
- `fetchReviewQueue` :222
- `submitReview` :228
- `updateReview` :238
- `deleteReview` :248
- `fetchDatasets` :259
- `fetchDatasetDetail` :265
- `runLeakageAudit` :271
- `fetchAllReviews` :279
- `buildDataset` :285
- `fetchDatasetImages` :299
- `fetchDatasetImageLabels` :312
- `fetchBatches` :391
- `fetchAvailableInspections` :448
- `fetchTrainingJobs` :617
- `fetchTrainingJobLogs` :632
- `fetchModelRegistryModels` :700

## 3. Crash Risk: Unguarded `res.json()`

Every `return res.json()` in the file is unguarded on the success path. If the server or a proxy returns non-JSON (HTML error page, 204 empty body, truncated body) on a 2xx response, `res.json()` throws a raw `SyntaxError` that surfaces as an unhelpful UI crash.

Only the second-style functions (from `reclassifyAnnotation` :324 onward) safely use `res.json().catch(() => ({ detail: res.statusText }))` — but only on the error path, never on the success path.

## 4. Deliberate Swallow

- `fetchDatasetAuditReport` :983 returns `null` on 404 by design. Callers must handle `null`; otherwise this is a silent-failure surface.

## 5. Structural Observation

No function in the file uses internal `try/catch`. All error propagation relies on callers. Any caller missing `.catch()` (or a React Query `onError` handler) will crash the UI or fail silently.

## Recommended Fixes (prioritized)

1. Add a shared `parseJsonSafe(res)` helper wrapping `res.json()` with `.catch()` and apply it to all success paths.
2. Standardize the error style: on `!res.ok`, read `detail` via `res.json().catch(...)` in all functions (currently ~21 functions use the weaker style).
3. Type `createNewDataset` with a proper response interface instead of `Promise<unknown>`.
4. Replace `Record<string, any>` in `BatchSummary.settings` and `createBatch` with a concrete settings type or `Record<string, unknown>`.
5. Remove the duplicate `BatchSummary` declaration (:437) and keep one canonical interface.

---

# Frontend Tailwind CSS Consistency Audit

Scope: 114 `.tsx` files under `frontend/src/components/`.

## 6. Hardcoded Palette Colors Instead of Semantic shadcn Variables

99 lines of hardcoded Tailwind palette classes (`red/blue/green/amber/...`) were found. No arbitrary hex values (`bg-[#...]`) were found in className strings. Notable clusters:

### 6.1 Duplicated status-badge pattern (should reuse `Shared/StatusBadge.tsx`)

The exact pattern `bg-<color>-500/15 text-<color>-700 dark:text-<color>-400 border-<color>-500/30` is copy-pasted in at least 8 files even though a shared `StatusBadge` component exists:

- `Shared/StatusBadge.tsx:7-13` (the canonical one)
- `Datasets/SplitStructurePanel.tsx:12-31`
- `Training/JobDetailPanel.tsx:17-21`
- `Platform/TaxonomyList.tsx:20-22`
- `Platform/CheckpointList.tsx:40-42, 215, 219`
- `Datasets/DatasetDetailPanel.tsx:103`
- `Inspection/gallery/ReviewFooter.tsx:85-88`
- `Experiments/RunComparisonTable.tsx:100-103`

### 6.2 Missing `dark:` variants — breaks dark mode (most glaring)

These use light-only palette shades with no dark-mode counterpart, inconsistent with the `dark:text-*-400` convention used everywhere else:

- `Models/DeployDialog.tsx:39-40` — `border-yellow-200 bg-yellow-50`, `text-yellow-800`
- `Models/RollbackDialog.tsx:25-26` — `border-red-200 bg-red-50`, `text-red-800`
- `Models/ModelRegistryDashboard.tsx:120, 124, 132` — `border-blue-200 bg-blue-50 text-blue-800`, `hover:text-blue-950`, `border-red-200 bg-red-50 text-red-800`
- `Models/ModelDetailPanel.tsx:105` — `text-green-600` / `text-red-600` (no dark variant)
- `Models/PromoteDialog.tsx:93, 112` — same
- `Inspection/export/ExportReportButton.tsx:39` and `Datasets/ReviewToDatasetBuilder.tsx:136, 145, 154` — `border-gray-300` (no dark variant; should be `border-border`)

### 6.3 Semantic roles hardcoded instead of tokens

- Success/error text: `text-green-600 dark:text-green-400` / `text-red-600 dark:text-red-400` repeated in `Datasets/ZipUploader.tsx:65`, `Datasets/LeakageAuditPanel.tsx:52-53`, `Inspection/ControlSidebar.tsx:321`, `Inspection/gallery/ReviewFooter.tsx:150` — candidates for `text-primary`/`text-destructive` or dedicated success tokens.
- `Datasets/ImageViewer.tsx:109, 129` — `hover:text-blue-500` / `hover:text-red-500` instead of `hover:text-primary` / `hover:text-destructive`.
- `Review/ReviewHistoryList.tsx:82` — `border-red-500/40 text-red-500 hover:bg-red-500/10` instead of `text-destructive` / `border-destructive`.

### 6.4 Hardcoded surfaces (acceptable but non-themable)

- `Training/JobDetailPanel.tsx:155-156` — terminal chrome: `bg-black/90`, `text-green-400`, `bg-black/50`, `border-white/10`, `text-gray-300`.
- `Datasets/ClassDistributionBar.tsx:9-11` — 12-color categorical chart palette; legitimate for charts but not theme-aware.

## 7. Card Padding / Rounding Inconsistencies

Card-like containers (`rounded-* border border-border bg-card p-*`) use 5 different paddings with no rule:

| Padding | Components |
|---|---|
| `p-8` | `Experiments/ExperimentDashboard.tsx:132`, `Datasets/ReviewToDatasetBuilder.tsx:80` (empty states) |
| `p-6` | `Datasets/NewDatasetDialog.tsx:71, 91`, `Datasets/ReviewToDatasetBuilder.tsx:95`, `Datasets/TileDialog.tsx:69, 109`, `Review/ReviewSubmitForm.tsx:22` |
| `p-5` | `Datasets/ImportPanel.tsx:10`, `Datasets/ReclassifyDialog.tsx:32` |
| `p-4` | `Training/JobDetailPanel.tsx:112`, `Datasets/LeakageAuditPanel.tsx:30`, `Datasets/DatasetAuditReport.tsx:15`, `Inspection/SummaryCard.tsx:16, 31`, `Inspection/ControlSidebar.tsx:290`, `Chains/ChainRunStatus.tsx:39` |
| `p-3` | `Models/ModelTrackCard.tsx:18`, `Inspection/SystemMetricsPanel.tsx:38`, `Inspection/ControlSidebar.tsx:525` |

Glaring inconsistencies:

1. **Same-tier Datasets panels disagree**: `LeakageAuditPanel` and `DatasetAuditReport` use `p-4`, `ImportPanel` uses `p-5`, `ReviewToDatasetBuilder` uses `p-6` — all are sibling panels in the Datasets tab.
2. **Dialogs disagree**: `ReclassifyDialog` uses `p-5` while `NewDatasetDialog` and `TileDialog` use `p-6` for the same modal-card shape.
3. **Rounding mixes within the same visual role**: `rounded-lg` (most panels) vs `rounded-md` (`ModelTrackCard`, `ChainRunStatus`) vs `rounded-sm` (`SummaryCard`, `SystemMetricsPanel`, `ControlSidebar`).
4. **Within one component**: `ReviewToDatasetBuilder` renders its empty state at `p-8` (:80) but its content at `p-6` (:95), so the card visibly jumps when data loads.

## Recommended Fixes (Tailwind)

1. Route all status chips through `Shared/StatusBadge.tsx` (extend its tone map if needed); delete the ~8 copy-pasted badge class strings.
2. Fix the Models dialogs/dashboards (DeployDialog, RollbackDialog, ModelRegistryDashboard, PromoteDialog, ModelDetailPanel) to use the `*-500/15 + dark:text-*-400` pattern or semantic tokens so dark mode renders correctly.
3. Replace `border-gray-300` with `border-border`, and success/error text with semantic tokens.
4. Standardize card containers: pick one padding per role (e.g., `p-4` for inline panels, `p-6` for dialogs) and one rounding (`rounded-lg`), ideally via the shadcn `Card` component instead of raw divs.

---

# Oversized Component Audit (> 250 lines)

8 of 114 `.tsx` files under `frontend/src/components/` exceed 250 lines:

| Lines | File | Primary purpose |
|---|---|---|
| 765 | `Inspection/ControlSidebar.tsx` | Inspection control panel: image upload, stage1/2/3 model selection, SAHI presets, device selection, pipeline toggles, batch run, view-stage switcher, display filters |
| 744 | `ui/sidebar.tsx` | Vendored shadcn/ui sidebar primitive (compound component with context) |
| 378 | `Training/LaunchTrainingDialog.tsx` | Dialog to launch training jobs in "direct" (raw params) or "recipe" mode |
| 342 | `Platform/CheckpointList.tsx` | Checkpoint registry table with scan, register dialog, and delete confirmation |
| 331 | `ui/chart.tsx` | Vendored shadcn/ui chart primitives (context + tooltip) |
| 331 | `Training/RecipeBuilder.tsx` | Dialog form to create training recipes (~20 fields: base strategy, freeze, LR mode, loss, hyperparams) |
| 273 | `Inspection/InspectionCanvas.tsx` | SVG canvas rendering panel polygons, defect masks, badges and legend over the inspected image |
| 254 | `Datasets/ReviewToDatasetBuilder.tsx` | Builds a dataset version from accumulated review verdicts (count cards, inclusion checkboxes, build form) |

## Extraction Recommendations

### `Inspection/ControlSidebar.tsx` (765) — worst offender
13 `useState` calls and 10+ visually distinct sections in one render. Extract:
1. **`UploadDropzone`** — drop zone + file input + progress (`:290-335`, `handleFile` :216, `handleDrop` :231)
2. **`StageModelSelect`** — the three nearly-identical Stage 1/2/3 model selects (`:337-354`, `:355-378`, `:469-491`) can be one reusable component parameterized by stage
3. **`Stage2InferenceControls`** — mode toggle grid + SAHI preset + direct-confidence slider (`:379-468`)
4. **`PipelineStageToggles`** — enable stage1/2/3 switches block (`:521-573`)
5. **`BatchRunSection`** — pending-files list + Run Batch button (`:574-637`, `runBatch`)
6. **`ViewStageSwitcher`** — 3-col stage-layer view grid (`:642-665`)
7. **`DisplayFilterSection`** — everything after the `Filters` heading (`:666-751`): confidence slider :732, DSI slider :747, panel/class toggles (`togglePanel` :245, `toggleClass` :251)

### `Training/LaunchTrainingDialog.tsx` (378)
- Extract the entire `{mode === "direct" && (...)}` block (`:172-374`) into a **`DirectLaunchForm`** sibling of the existing `RecipeLaunchForm`; the dialog then only orchestrates the mode toggle.
- Extract `handleLoadTemplate` (:57) + template state into a **`useConfigTemplate(stage)`** hook; the `useEffect` at :24-26 calling it before its declaration is also a latent TDZ/lint smell this would fix.

### `Platform/CheckpointList.tsx` (342)
- **`RegisterCheckpointDialog`** — the `<Dialog>` block `:246-313` plus `handleRegister` (:103) and its form state
- **`DeleteCheckpointDialog`** — the `<AlertDialog>` block `:314-339` plus `handleDelete` (:132)
- **`CheckpointTable`** — the `<table>` block `:184-245` (origin badges via shared `StatusBadge`)

### `Training/RecipeBuilder.tsx` (331)
~20 flat `useState` fields (`:41-66`) is unmaintainable. Extract field clusters as sub-forms (or collapse into one `useReducer` state object):
- **`BaseStrategyFields`** — base strategy + checkpoint select (`:135+`)
- **`FreezeFields`** — freeze mode + layers
- **`LrFields`** — lr mode, split layer, backbone mult
- **`LossFields`** — loss type + focal loss gamma/alpha/scale
- **`TrainingHyperparamFields`** — imgsz, batch, epochs, optimizer, lr0, lrf, patience

### `Inspection/InspectionCanvas.tsx` (273)
One render function draws three SVG layers. Extract:
- **`PanelPolygonLayer`** — panel polygons + labels (polygons at :115, :139)
- **`DefectPolygonLayer`** — defect masks filtered by `defectMatchesViewStage` (:19, polygon at :245)
- **`CanvasLegend`** — the legend/badge strip below the SVG
- Move `toPoints` (:15) into a shared geometry util if reused.

### `Datasets/ReviewToDatasetBuilder.tsx` (254)
- **`ReviewCountCards`** — the 4-count stat grid (`:102-124`)
- **`InclusionToggles`** — confirmed/rejected/unclear checkboxes (`:136-160`)
- **`BuildResultBanner`** — success/result block (`:243-250`)
- Keep `handleBuild` (:57) in the parent or move into a `useBuildDataset` hook.

### `ui/sidebar.tsx` (744) and `ui/chart.tsx` (331)
Vendored shadcn/ui primitives — do **not** split; they are library components maintained upstream. If they drift, prefer re-vendoring over hand-editing.

## Priority Order
1. `ControlSidebar.tsx` (765 lines, 13 state vars, 7 natural sub-components)
2. `RecipeBuilder.tsx` (20 loose state fields)
3. `LaunchTrainingDialog.tsx` (clean 2-mode split already half-done)
4. `CheckpointList.tsx` (two dialogs + table are trivially separable)
5. `InspectionCanvas.tsx`, `ReviewToDatasetBuilder.tsx` (moderate gains)

---

# Dialog UX Safety Audit

11 `*Dialog.tsx` files audited for three patterns: **A)** `Loader2` spinner on submit during API calls, **B)** `disabled` when invalid/loading, **C)** sonner toast for success/error.

| Dialog | Spinner (A) | Disabled (B) | Toast (C) |
|---|---|---|---|
| `Inspection/PastBatchesDialog.tsx` | ✅ :125 | ✅ :121 | ✅ 5 toasts (delete/rename/load) |
| `Surgery/HeadSurgeryDialog.tsx` | ✅ 3 uses | ✅ `!canSubmit` | ✅ 2 toasts |
| `Datasets/ReclassifyDialog.tsx` | ✅ :68 | ✅ :65 `saving \|\| selectedClass === currentClassId` | ❌ inline error only (:59) |
| `Datasets/TileDialog.tsx` | ✅ :222 | ✅ :218 `!newDatasetId.trim() \|\| submitting` | ❌ inline error (:210) + result state |
| `Datasets/ResplitDialog.tsx` | ✅ | ✅ `!canSubmit` :152 | ❌ inline error (:146) + result state |
| `Datasets/NewDatasetDialog.tsx` | ✅ 3 uses | ✅ 2 uses | ❌ inline error only (:171) |
| `Training/LaunchTrainingDialog.tsx` | ✅ :364 | ✅ :361 `submitting \|\| !datasetPath` | ❌ inline error only (:338) |
| `Models/RollbackDialog.tsx` | ❌ text-only "Rolling back..." :42 | ✅ :40 `isLoading` | ❌ none — parent shows inline `actionMessage` banner |
| `Models/DeployDialog.tsx` | ❌ text-only "Deploying..." :60 | ✅ :59 `isLoading` | ❌ none — same parent banner |
| `Models/PromoteDialog.tsx` | ❌ text-only "Promoting..." :108 | ✅ :107 `isLoading \|\| !allPassed` | ❌ none — same parent banner |
| `Shared/ConfirmDialog.tsx` | ❌ no loading affordance | ❌ no `disabled` wiring | ❌ delegated to caller |

## Missing Patterns

### No loading spinner (4 dialogs)
1. **`Models/RollbackDialog.tsx`**, **`DeployDialog.tsx`**, **`PromoteDialog.tsx`** — receive `isLoading` and disable buttons, but only swap button text; no `Loader2` icon like every other dialog.
2. **`Shared/ConfirmDialog.tsx`** — `AlertDialogAction` fires `onConfirm` and closes instantly with no loading state. Since 5 callers use it for destructive async actions (delete recipe/dataset/inspection/batch), slow API calls give zero in-flight feedback. Add an optional `isLoading` prop that disables the action and shows `Loader2`.

### No sonner toast (9 dialogs)
- Only `PastBatchesDialog` and `HeadSurgeryDialog` use `toast.success`/`toast.error`.
- The 4 Datasets dialogs + `LaunchTrainingDialog` show errors as small inline `<p className="text-xs text-destructive">` lines and render success as inline banners or silent `onCreated()` callbacks — easy to miss, inconsistent with the toast convention used elsewhere in the app.
- The 3 Models dialogs delegate feedback to `ModelRegistryDashboard`'s inline `actionMessage` banner (`ModelRegistryDashboard.tsx:29, 119`) — success and error share one dismissible strip, no toast.

### Disabled-state gaps
- All audited dialogs with API submits have at least one `disabled` guard — no outright misses. Notable good examples: `ReclassifyDialog` also disables when the class is unchanged (`:65`), `PromoteDialog` blocks on failed gates (`:107`).
- `ConfirmDialog` is the only one with zero `disabled` logic (see above).
- `RollbackDialog`'s confirm has no form-validation guard, but it's a bare confirmation so this is acceptable.

## Recommendations
1. Add `Loader2` spinners to the three Models dialogs (one-line change each, `isLoading` already available).
2. Extend `Shared/ConfirmDialog.tsx` with `isLoading?: boolean` → `disabled` + spinner on `AlertDialogAction`.
3. Standardize on sonner: replace inline error `<p>` + result banners in the 7 non-toast dialogs with `toast.success`/`toast.error` (keep inline errors only for form-field-level validation like `LaunchTrainingDialog`'s JSON parse check).
4. `ModelRegistryDashboard`'s `actionMessage` banner can be retired in favor of toasts once the dialogs own their own feedback.

Suggested commit: `docs: append dialog UX safety audit to report_frontend.md`

---

# React Anti-Pattern Audit (routes)

Files: `frontend/src/routes/training.tsx` (10 lines), `frontend/src/routes/datasets.tsx` (148 lines). Since `training.tsx` only renders `<TrainingDashboard />`, its delegate `components/Training/TrainingDashboard.tsx` (145 lines) was audited as the effective training-page logic.

## `routes/training.tsx` (:1-10)
Pure delegation — no hooks, no anti-patterns. All findings below are in `TrainingDashboard.tsx`.

## `routes/datasets.tsx`

### 1. `useEffect` with empty deps referencing a render-body function (:41-43)
```tsx
useEffect(() => { loadDatasets(); }, []);
```
`loadDatasets` (:29) is recreated every render but omitted from deps. Functionally safe here (mount-only fetch), but it violates `react-hooks/exhaustive-deps` and means any future dependency added to `loadDatasets` will silently go stale. Fix: wrap `loadDatasets` in `useCallback` and list it in deps.

### 2. Unstable function identities passed to children (missing `useCallback`)
No component in `Datasets/` or `Training/` is wrapped in `React.memo` (verified), so today these cause no extra child re-renders beyond the parent's own renders — but they defeat any future memoization and are anti-patterns:
- `loadDatasets` :29 → passed as `onCreated` to `NewDatasetDialog` :144
- `handleSelect` :45 → passed as `onSelect` to `DatasetListView` :141
- `handleBack` :58 / `refreshDetail` :62 → passed to `DatasetDetailPanel` :130-131
- `handleOpenBuilder` :72 → `Button onClick` :93
- `handleBackFromBuilder` :77 → passed to `ReviewToDatasetBuilder` :124

### 3. Inline arrow prop recreated every render (:144)
`onClose={() => setShowNewDialog(false)}` — new reference each render; same class of issue as above.

### 4. No infinite-loop risk
- No effect depends on state it also writes.
- `refreshDetail` :62 reads `selectedDetail` but is only invoked from event handlers, never from an effect.
- `useEffect` at :41 runs once (`[]`), so `setLoading`/`setDatasets` inside cannot re-trigger it.

## `components/Training/TrainingDashboard.tsx` (delegate of training.tsx)

### 1. Polling effect resets `loading` every 5 seconds (:28-44) — real bug risk
```tsx
const loadJobs = async () => { setLoading(true); ... };
useEffect(() => { loadJobs(); const interval = setInterval(loadJobs, 5000); ... }, []);
```
`loadJobs` calls `setLoading(true)` (:30) on **every** poll tick. Any UI gated on `loading` (skeletons, empty-state flicker) will re-flash every 5s for the lifetime of the page. Fix: only set `loading` on the initial fetch (e.g., a `silent` parameter or separate `initialLoad` flag), or drop the global `loading` from polling updates.

### 2. `useEffect` deps violation (:40-44)
`loadJobs` (render-body function :28) is captured by the effect and the interval but missing from deps. Same lint violation as datasets.tsx; safe today only because `loadJobs` closes over no changing state — but it does read `fetchTrainingJobs` results and calls `toast`; any future state dependency would go stale inside the interval closure.

### 3. Interval keeps running in detail view (:73-76)
Early return renders `JobDetailPanel` when `selectedJobId` is set, but the 5s `loadJobs` interval keeps firing (and resetting `loading`) in the background. Wasted requests; harmless but wasteful.

### 4. Unstable callbacks
- `onBack={() => setSelectedJobId(null)}` inline arrow :76
- `handleStopJob` :48, `confirmStopJob` :50, `handlePresetSelect` :63, `handleRecipeSaved` :68 defined in render body and passed to `JobListTable`, `ConfirmDialog`, `StrategyPresetPicker`, `RecipeList`.

### 5. No infinite-loop risk
Polling writes `jobs`/`loading` which no effect depends on; `recipesRefreshKey` is a manual bump key, not effect-driven.

## Summary Table

| File | Line(s) | Anti-pattern | Severity |
|---|---|---|---|
| `routes/datasets.tsx` | 41-43 | `useEffect` deps missing `loadDatasets` | Low (lint) |
| `routes/datasets.tsx` | 29, 45, 58, 62, 72, 77 | Render-body handlers passed as props without `useCallback` | Low |
| `routes/datasets.tsx` | 144 | Inline arrow `onClose` | Low |
| `Training/TrainingDashboard.tsx` | 30 + 42 | **Polling resets `loading=true` every 5s** | Medium (UI flicker) |
| `Training/TrainingDashboard.tsx` | 40-44 | `useEffect` deps missing `loadJobs` | Low (lint) |
| `Training/TrainingDashboard.tsx` | 73-76 | Interval continues during detail view | Low |
| `Training/TrainingDashboard.tsx` | 48-71 | Render-body handlers without `useCallback` | Low |
| Both | — | Infinite loops | None found |

## Recommendations
1. Fix the polling flicker: `loadJobs(silent = true)` that skips `setLoading` on interval ticks (TrainingDashboard :28-44).
2. Wrap `loadDatasets` / `loadJobs` in `useCallback` and include them in effect deps to satisfy `react-hooks/exhaustive-deps`.
3. Apply `useCallback` to the six handlers in `datasets.tsx` and the four in `TrainingDashboard.tsx` before introducing `React.memo` on child panels.
4. Optional: pause the jobs interval when `selectedJobId` is set.

Suggested commit: `docs: append react anti-pattern audit to report_frontend.md`
