import { useCallback, useEffect, useMemo, useReducer } from "react";
import type {
  DefectClass,
  InspectionPayload,
  PanelId,
  PipelineStage,
  ViewStage,
} from "@/lib/inspection/schema";

export interface BatchItem {
  inspectionId: string;
  filename: string;
  thumbnail: string;
  fullUrl?: string;
  payload: InspectionPayload;
}

export interface BatchState {
  items: BatchItem[];
  selectedIndex: number | null;
  totalMs: number;
  deviceUsed: string;
}
import { runInspection } from "@/lib/inspection/apiClient";

function base64ToFile(base64: string, filename: string): File | null {
  try {
    const arr = base64.split(",");
    if (arr.length < 2) return null;
    const mime = arr[0].match(/:(.*?);/)?.[1] || "image/jpeg";
    const bstr = atob(arr[1]);
    let n = bstr.length;
    const u8arr = new Uint8Array(n);
    while (n--) {
      u8arr[n] = bstr.charCodeAt(n);
    }
    return new File([u8arr], filename, { type: mime });
  } catch (e) {
    console.warn("Failed to convert base64 to file:", e);
    return null;
  }
}

export interface Filters {
  panels: Set<PanelId>;
  classes: Set<DefectClass>;
  minConfidence: number;
  minDsi: number;
}

export interface StageToggles {
  enableStage1?: boolean;
  enableStage2?: boolean;
  enableStage3?: boolean;
}

interface State {
  imageUrl: string | null;
  imageName: string | null;
  imageFile: File | null;
  stage: PipelineStage;
  message: string;
  payload: InspectionPayload | null;
  filters: Filters;
  viewStage: ViewStage;
  enableStage1: boolean;
  enableStage2: boolean;
  enableStage3: boolean;
  batch: BatchState | null;
  pendingFiles: File[] | null; // Files waiting to be processed
}

type Action =
  | { type: "set_image"; url: string; name: string; file: File | null }
  | { type: "stage"; stage: PipelineStage; message: string }
  | { type: "payload"; payload: InspectionPayload }
  | { type: "reset" }
  | { type: "filters"; patch: Partial<Filters> }
  | { type: "view_stage"; viewStage: ViewStage }
  | { type: "stage_toggles"; patch: StageToggles }
  | { type: "hydrate"; state: Partial<State> }
  | { type: "set_pending_files"; files: File[] }
  | { type: "set_batch"; batch: BatchState }
  | { type: "select_batch_item"; index: number | null };

const STORAGE_KEY = "car_defect_inspection_state";

const initialFilters: Filters = {
  panels: new Set(),
  classes: new Set(),
  minConfidence: 0,
  minDsi: 0,
};

const initial: State = {
  imageUrl: null,
  imageName: null,
  imageFile: null,
  stage: "idle",
  message: "Awaiting image.",
  payload: null,
  filters: initialFilters,
  viewStage: 2,
  enableStage1: true,
  enableStage2: true,
  enableStage3: true,
  batch: null,
  pendingFiles: null,
};

// Helper to serialize state for localStorage (excludes File object and non-serializable Sets)
function serializeState(state: State) {
  return {
    imageUrl: state.imageUrl,
    imageName: state.imageName,
    stage: state.stage,
    message: state.message,
    payload: state.payload,
    viewStage: state.viewStage,
    enableStage1: state.enableStage1,
    enableStage2: state.enableStage2,
    enableStage3: state.enableStage3,
    filters: {
      panels: Array.from(state.filters.panels),
      classes: Array.from(state.filters.classes),
      minConfidence: state.filters.minConfidence,
      minDsi: state.filters.minDsi,
    },
    batch: state.batch
      ? {
          ...state.batch,
          items: state.batch.items.map(({ fullUrl, ...rest }) => rest),
        }
      : null,
  };
}

function reducer(state: State, action: Action): State {
  switch (action.type) {
    case "set_image":
      return {
        ...state,
        imageUrl: action.url,
        imageName: action.name,
        imageFile: action.file,
        stage: "idle",
        payload: null, // Clear old results when a new image is loaded
        message: "Ready to inspect.",
      };
    case "stage":
      return { ...state, stage: action.stage, message: action.message };
    case "payload":
      return { ...state, payload: action.payload };
    case "reset":
      localStorage.removeItem(STORAGE_KEY);
      return { ...initial, filters: initialFilters };
    case "filters":
      return { ...state, filters: { ...state.filters, ...action.patch } };
    case "view_stage":
      return { ...state, viewStage: action.viewStage };
    case "stage_toggles":
      return { ...state, ...action.patch };
    case "set_pending_files":
      return {
        ...state,
        pendingFiles: action.files,
        batch: null,
        stage: "idle",
        message: `${action.files.length} images queued. Configure settings and click "Run Batch".`,
      };
    case "set_batch": {
      return {
        ...state,
        batch: action.batch,
        pendingFiles: null,
        // Don't set imageUrl/imageName/payload — keep batch in "grid view"
        imageUrl: null,
        imageName: null,
        payload: null,
        stage: "done",
        message: `Batch complete. ${action.batch.items.length} images processed. Click a thumbnail to inspect.`,
      };
    }
    case "select_batch_item": {
      if (!state.batch) return state;
      if (action.index === null) {
        // Back to batch grid view — MUST reset selectedIndex or the grid never renders
        return {
          ...state,
          batch: { ...state.batch, selectedIndex: null },
          imageUrl: null,
          imageName: null,
          imageFile: null,
          payload: null,
          stage: "done",
          message: `Batch view — ${state.batch.items.length} images. Click a thumbnail to inspect.`,
        };
      }
      const item = state.batch.items[action.index];
      return {
        ...state,
        batch: { ...state.batch, selectedIndex: action.index },
        imageUrl: item.fullUrl ?? item.thumbnail,
        imageName: item.filename,
        payload: item.payload,
        stage: "done",
        message: `Viewing ${action.index + 1} of ${state.batch.items.length}`,
      };
    }
    case "hydrate":
      return { ...state, ...action.state };
  }
}

export function useInspection(defaults: { imageUrl: string; imageName: string }) {
  const [state, dispatch] = useReducer(reducer, {
    ...initial,
    imageUrl: defaults.imageUrl,
    imageName: defaults.imageName,
    message: "Demo vehicle loaded. Ready to inspect.",
  });

  useEffect(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        const hydratedFilters: Filters = {
          panels: new Set(parsed.filters?.panels || []),
          classes: new Set(parsed.filters?.classes || []),
          minConfidence: parsed.filters?.minConfidence ?? 0,
          minDsi: parsed.filters?.minDsi ?? 0,
        };

        const hydratedFile =
          parsed.imageUrl && parsed.imageName
            ? base64ToFile(parsed.imageUrl, parsed.imageName)
            : null;
        // Restored batches always open in grid view (object URLs are dead after refresh)
        const hydratedBatch = parsed.batch ? { ...parsed.batch, selectedIndex: null } : null;
        dispatch({
          type: "hydrate",
          state: {
            imageUrl: hydratedBatch ? null : parsed.imageUrl,
            imageName: hydratedBatch ? null : parsed.imageName,
            imageFile: hydratedBatch ? null : hydratedFile,
            stage: parsed.stage || "idle",
            message: hydratedBatch
              ? `Batch restored: ${hydratedBatch.items.length} images.`
              : parsed.message || "Restored from previous session.",
            payload: hydratedBatch ? null : parsed.payload,
            batch: hydratedBatch,
            viewStage: parsed.viewStage || 2,
            enableStage1: parsed.enableStage1 ?? true,
            enableStage2: parsed.enableStage2 ?? true,
            enableStage3: parsed.enableStage3 ?? true,
            filters: hydratedFilters,
          },
        });
      }
    } catch (e) {
      console.warn("Failed to hydrate inspection state:", e);
    }
  }, []);

  useEffect(() => {
    try {
      if (state.imageUrl === defaults.imageUrl && !state.payload && !state.batch) return;
      localStorage.setItem(STORAGE_KEY, JSON.stringify(serializeState(state)));
    } catch (e) {
      if (e instanceof DOMException && e.name === "QuotaExceededError") {
        console.warn("localStorage quota exceeded. Saving state without image data.");
        const stateWithoutImage = serializeState(state);
        stateWithoutImage.imageUrl = null;
        stateWithoutImage.imageName = null;
        stateWithoutImage.batch = null;
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(stateWithoutImage));
        } catch (e2) {
          console.warn("Failed to save inspection state even without image:", e2);
        }
      } else {
        console.warn("Failed to save inspection state:", e);
      }
    }
  }, [state, defaults.imageUrl]);

  const setImage = useCallback((url: string, name: string, file: File) => {
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const base64Url = e.target?.result as string;
        dispatch({ type: "set_image", url: base64Url, name, file });
      };
      reader.readAsDataURL(file);
    } else {
      dispatch({ type: "set_image", url, name, file: null });
    }
  }, []);

  const run = useCallback(
    async (opts?: {
      forceClean?: boolean;
      modelName?: string;
      stage2ModelName?: string;
      stage2Mode?: "direct" | "sahi";
      stage2Preset?: "balanced" | "safety" | "max_recall";
      stage2Conf?: number;
      device?: string;
    }) => {
      dispatch({
        type: "stage",
        stage: "processing",
        message: "Running inspection pipeline...",
      });
      dispatch({ type: "payload", payload: null as never });

      if (!state.imageFile) {
        dispatch({
          type: "stage",
          stage: "error",
          message: "No image file available. Please upload an image.",
        });
        return;
      }

      try {
        const payload = await runInspection({
          file: state.imageFile,
          modelName: opts?.modelName,
          stage2ModelName: opts?.stage2ModelName,
          stage2Mode: opts?.stage2Mode,
          stage2Preset: opts?.stage2Preset,
          stage2Conf: opts?.stage2Conf,
          device: opts?.device,
          enableStage1: state.enableStage1,
          enableStage2: state.enableStage2,
          enableStage3: state.enableStage3,
        });
        dispatch({ type: "payload", payload });
        dispatch({
          type: "stage",
          stage: "done",
          message: "Inspection complete.",
        });
      } catch (err) {
        console.error("Inspection failed:", err);
        dispatch({
          type: "stage",
          stage: "error",
          message: err instanceof Error ? err.message : "Inspection failed.",
        });
      }
    },
    [state.imageFile, state.enableStage1, state.enableStage2, state.enableStage3],
  );

  const reset = useCallback(() => dispatch({ type: "reset" }), []);

  const setFilters = useCallback(
    (patch: Partial<Filters>) => dispatch({ type: "filters", patch }),
    [],
  );

  const setViewStage = useCallback(
    (viewStage: ViewStage) => dispatch({ type: "view_stage", viewStage }),
    [],
  );

  const setStageToggles = useCallback(
    (patch: StageToggles) => dispatch({ type: "stage_toggles", patch }),
    [],
  );

  const filteredDefects = useMemo(() => {
    if (!state.payload) return [];
    const { panels, classes, minConfidence, minDsi } = state.filters;
    return state.payload.defects.filter((d) => {
      if (panels.size && !panels.has(d.panel)) return false;
      if (classes.size && !classes.has(d.class)) return false;
      if (d.confidence < minConfidence) return false;
      if (d.dsi != null && d.dsi < minDsi) return false;
      return true;
    });
  }, [state.payload, state.filters]);

  const setPendingFiles = useCallback((files: File[]) => {
    dispatch({ type: "set_pending_files", files });
  }, []);

  const setBatch = useCallback((batch: BatchState) => {
    dispatch({ type: "set_batch", batch });
  }, []);

  const selectBatchItem = useCallback((index: number | null) => {
    dispatch({ type: "select_batch_item", index });
  }, []);

  return {
    state,
    filteredDefects,
    setImage,
    run,
    reset,
    setFilters,
    setViewStage,
    setStageToggles,
    setPendingFiles,
    setBatch,
    selectBatchItem,
  };
}
