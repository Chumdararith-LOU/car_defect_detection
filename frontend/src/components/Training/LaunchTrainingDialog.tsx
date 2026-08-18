import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Loader2, Play } from "lucide-react";
import type { DatasetSummary, DatasetStage } from "@/lib/inspection/schema";
import type { LaunchTrainingRequest, TrainingStage } from "@/lib/inspection/trainingSchema";
import { fetchDatasets, launchTrainingJob, fetchConfigTemplate } from "@/lib/inspection/apiClient";
import { RecipeLaunchForm } from "./RecipeLaunchForm";

interface Props {
  onClose: () => void;
  onLaunched: () => void;
}

export function LaunchTrainingDialog({ onClose, onLaunched }: Props) {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [loadingDatasets, setLoadingDatasets] = useState(true);

  const [mode, setMode] = useState<"direct" | "recipe">("direct");
  const [stage, setStage] = useState<TrainingStage>("stage2");

  // Auto-load template when stage changes

  useEffect(() => {
    handleLoadTemplate();
  }, [stage]);
  const [datasetPath, setDatasetPath] = useState("");
  const [configPath, setConfigPath] = useState("");
  const [baseModel, setBaseModel] = useState("");
  const [device, setDevice] = useState("0");
  const [projectName, setProjectName] = useState("");
  const [runName, setRunName] = useState("");
  const [epochs, setEpochs] = useState<number | "">(100);
  const [imgsz, setImgsz] = useState<number | "">(640);
  const [batchSize, setBatchSize] = useState<number | "">(8);

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [advancedJson, setAdvancedJson] = useState("{}");

  const [submitting, setSubmitting] = useState(false);
  const [loadingTemplate, setLoadingTemplate] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDatasets()
      .then((res) => {
        setDatasets(res.datasets);
        // Auto-select first dataset if available
        if (res.datasets.length > 0) {
          setDatasetPath(res.datasets[0].yaml_path);
        }
      })
      .catch(() => setError("Failed to load datasets"))
      .finally(() => setLoadingDatasets(false));
  }, []);

  const handleLoadTemplate = async () => {
    setLoadingTemplate(true);
    setError(null);
    try {
      const res = await fetchConfigTemplate(stage);
      const tmpl = res.template;

      // Populate flat fields if they exist in the template
      if (tmpl.project_name) setProjectName(tmpl.project_name);
      if (tmpl.run_name) setRunName(tmpl.run_name);
      if (tmpl.model_preset) setBaseModel(tmpl.model_preset);
      if (tmpl.device) setDevice(String(tmpl.device));

      // Populate simple fields from template
      if (tmpl.epochs) setEpochs(tmpl.epochs);
      if (tmpl.imgsz) setImgsz(tmpl.imgsz);
      if (tmpl.batch_size) setBatchSize(tmpl.batch_size);

      // Put remaining fields into advanced JSON
      const { epochs: _, imgsz: __, batch_size: ___, ...rest } = tmpl;
      if (Object.keys(rest).length > 0) {
        setShowAdvanced(true);
        setAdvancedJson(JSON.stringify(rest, null, 2));
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load template");
    } finally {
      setLoadingTemplate(false);
    }
  };

  const handleLaunch = async () => {
    if (!datasetPath) {
      setError("Please select a dataset.");
      return;
    }

    // Build overrides from simple fields
    const overrides: Record<string, unknown> = {};
    if (epochs !== "") overrides.epochs = epochs;
    if (imgsz !== "") overrides.imgsz = imgsz;
    if (batchSize !== "") overrides.batch_size = batchSize;

    // Merge advanced JSON if provided
    if (showAdvanced && advancedJson.trim()) {
      try {
        const advanced = JSON.parse(advancedJson);
        Object.assign(overrides, advanced);
      } catch {
        setError("Invalid JSON in Advanced Overrides field.");
        return;
      }
    }

    setSubmitting(true);
    setError(null);

    const request: LaunchTrainingRequest = {
      stage,
      dataset_path: datasetPath,
      config_path: configPath || undefined,
      base_model: baseModel || undefined,
      device,
      project_name: projectName || undefined,
      run_name: runName || undefined,
      overrides,
    };

    try {
      await launchTrainingJob(request);
      onLaunched();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to launch job");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog
      open
      onOpenChange={(o) => {
        if (!o) onClose();
      }}
    >
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto space-y-4">
        <DialogHeader>
          <DialogTitle>Launch Training Job</DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-1 rounded-md border border-border p-1">
          <button
            type="button"
            onClick={() => setMode("direct")}
            className={
              mode === "direct"
                ? "rounded-sm bg-muted px-3 py-1.5 text-xs font-medium"
                : "rounded-sm px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
            }
          >
            Direct config
          </button>
          <button
            type="button"
            onClick={() => setMode("recipe")}
            className={
              mode === "recipe"
                ? "rounded-sm bg-muted px-3 py-1.5 text-xs font-medium"
                : "rounded-sm px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground"
            }
          >
            Recipe
          </button>
        </div>
        {mode === "recipe" && <RecipeLaunchForm onClose={onClose} onLaunched={onLaunched} />}
        {mode === "direct" && (
          <>
            <div className="space-y-3">
              {/* Stage */}
              <div className="space-y-1.5">
                <div className="flex items-center justify-between">
                  <label className="text-sm font-medium">Stage</label>
                  <button
                    type="button"
                    onClick={handleLoadTemplate}
                    disabled={loadingTemplate}
                    className="text-xs text-primary hover:underline flex items-center gap-1"
                  >
                    {loadingTemplate ? "Loading..." : "Load Champion Defaults"}
                  </button>
                </div>
                <select
                  value={stage}
                  onChange={(e) => setStage(e.target.value as TrainingStage)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                >
                  <option value="stage1">Stage 1 (SOD / Anomaly)</option>
                  <option value="stage2">Stage 2 (7-class Defect)</option>
                  <option value="stage3">Stage 3 (21-class Panel)</option>
                </select>
              </div>

              {/* Dataset */}
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Dataset</label>
                {loadingDatasets ? (
                  <p className="text-xs text-muted-foreground">Loading datasets...</p>
                ) : (
                  <select
                    value={datasetPath}
                    onChange={(e) => setDatasetPath(e.target.value)}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono"
                  >
                    {datasets.map((d) => (
                      <option key={d.dataset_id} value={d.yaml_path}>
                        {d.name} ({d.stage})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {/* Config & Base Model */}
              <div className="grid grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">
                    Config Path (Optional)
                  </label>
                  <input
                    type="text"
                    value={configPath}
                    onChange={(e) => setConfigPath(e.target.value)}
                    placeholder="configs/stage2/train.yaml"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs font-mono"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">
                    Base Model (Optional)
                  </label>
                  <input
                    type="text"
                    value={baseModel}
                    onChange={(e) => setBaseModel(e.target.value)}
                    placeholder="yolo26m-seg.pt"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs font-mono"
                  />
                </div>
              </div>

              {/* Device & Project/Run */}
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Device</label>
                  <input
                    type="text"
                    value={device}
                    onChange={(e) => setDevice(e.target.value)}
                    placeholder="0"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs font-mono"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Project Name</label>
                  <input
                    type="text"
                    value={projectName}
                    onChange={(e) => setProjectName(e.target.value)}
                    placeholder="stage2_exp"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Run Name</label>
                  <input
                    type="text"
                    value={runName}
                    onChange={(e) => setRunName(e.target.value)}
                    placeholder="run_01"
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs"
                  />
                </div>
              </div>

              {/* Simple Overrides */}
              <div className="grid grid-cols-3 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Epochs</label>
                  <input
                    type="number"
                    min={1}
                    value={epochs}
                    onChange={(e) => setEpochs(e.target.value === "" ? "" : Number(e.target.value))}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Image Size</label>
                  <input
                    type="number"
                    min={32}
                    step={32}
                    value={imgsz}
                    onChange={(e) => setImgsz(e.target.value === "" ? "" : Number(e.target.value))}
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-muted-foreground">Batch Size</label>
                  <input
                    type="number"
                    min={1}
                    value={batchSize}
                    onChange={(e) =>
                      setBatchSize(e.target.value === "" ? "" : Number(e.target.value))
                    }
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                  />
                </div>
              </div>

              {/* Advanced JSON (optional) */}
              <div className="space-y-1.5">
                <button
                  type="button"
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="text-xs text-primary hover:underline"
                >
                  {showAdvanced ? "Hide" : "Show"} Advanced Overrides (JSON)
                </button>
                {showAdvanced && (
                  <textarea
                    value={advancedJson}
                    onChange={(e) => setAdvancedJson(e.target.value)}
                    placeholder='{"lr0": 0.01, "momentum": 0.937}'
                    className="w-full rounded-md border border-input bg-background px-3 py-2 text-xs font-mono min-h-[80px]"
                  />
                )}
              </div>
            </div>

            {error && <p className="text-xs text-destructive">{error}</p>}

            {/* Mac Safety Warning */}
            {(() => {
              const currentEpochs = typeof epochs === "number" ? epochs : 100;
              const isLongRun = currentEpochs > 5;

              if (isLongRun) {
                return (
                  <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-400">
                    <strong>⚠️ Long Training Detected:</strong> {currentEpochs} epochs may take
                    several hours on Mac. Consider reducing to 1-5 epochs for testing, or use a
                    remote GPU server.
                  </div>
                );
              }
              return null;
            })()}

            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={onClose}>
                Cancel
              </Button>
              <Button onClick={handleLaunch} disabled={submitting || !datasetPath}>
                {submitting ? (
                  <>
                    <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> Launching...
                  </>
                ) : (
                  <>
                    <Play className="mr-1.5 h-4 w-4" /> Launch Job
                  </>
                )}
              </Button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
