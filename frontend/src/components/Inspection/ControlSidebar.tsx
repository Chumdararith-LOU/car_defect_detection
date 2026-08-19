import { useEffect, useRef, useState, type ChangeEvent, type DragEvent } from "react";
import { Upload, Play, RefreshCw, Download, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { Progress } from "@/components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import {
  fetchModels,
  fetchSystemDevices,
  runInspection,
  type Stage2Mode,
  type Stage2Preset,
  type SystemDevices,
} from "@/lib/inspection/apiClient";
import { SystemMetricsPanel } from "./SystemMetricsPanel";
import type {
  DefectClass,
  PanelId,
  PipelineStage,
  InspectionPayload,
  ViewStage,
} from "@/lib/inspection/schema";
import { DEFECT_CLASSES, ALL_PANELS, PANEL_LABELS } from "@/lib/inspection/constants";
import type { Filters, StageToggles } from "@/hooks/useInspection";
import { StageStatus } from "./StageStatus";
import { cn } from "@/lib/utils";
import { createBatch } from "@/lib/inspection/apiClient";

const VIEW_STAGES: { id: ViewStage; label: string }[] = [
  { id: 1, label: "Pre-Screen" },
  { id: 2, label: "Defects" },
  { id: 3, label: "Context" },
];

interface Props {
  imageName: string | null;
  stage: PipelineStage;
  message: string;
  payload: InspectionPayload | null;
  filters: Filters;
  viewStage?: ViewStage;
  onImage: (file: File) => void;
  onRun: (opts?: {
    forceClean?: boolean;
    modelName?: string;
    stage2ModelName?: string;
    stage2Mode?: "direct" | "sahi";
    stage2Preset?: "balanced" | "safety" | "max_recall";
    stage2Conf?: number;
    device?: string;
  }) => void;
  onReset: () => void;
  onFilters: (patch: Partial<Filters>) => void;
  onViewStage?: (v: ViewStage) => void;
  enableStage1: boolean;
  enableStage2: boolean;
  enableStage3: boolean;
  onStageToggles: (patch: StageToggles) => void;
  pendingFiles: File[] | null;
  onSetPendingFiles: (files: File[]) => void;
  onRunBatch: (items: any[], totalMs: number) => void;
  onOpenPastBatches: () => void;
}
export function ControlSidebar({
  imageName,
  stage,
  message,
  payload,
  filters,
  viewStage = 2,
  onImage,
  onRun,
  onReset,
  onFilters,
  onViewStage,
  enableStage1,
  enableStage2,
  enableStage3,
  onStageToggles,
  pendingFiles,
  onSetPendingFiles,
  onRunBatch,
  onOpenPastBatches,
}: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [models, setModels] = useState<string[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [selectedStage2Model, setSelectedStage2Model] = useState<string>("");
  const [stage2Mode, setStage2Mode] = useState<Stage2Mode>("direct");
  const [stage2Preset, setStage2Preset] = useState<Stage2Preset>("balanced");
  const [stage2Conf, setStage2Conf] = useState<number>(0.15);
  const [devices, setDevices] = useState<SystemDevices | null>(null);
  const [device, setDevice] = useState<string>("auto");
  const [stage2Models, setStage2Models] = useState<string[]>([]);
  const [stage3Models, setStage3Models] = useState<string[]>([]);
  const [selectedStage3Model, setSelectedStage3Model] = useState<string>("");

  useEffect(() => {
    fetch((import.meta.env.VITE_API_BASE || "http://localhost:8010") + "/api/models")
      .then((res) => res.json())
      .then((data) => {
        // Stage 1
        const s1 = data.models || data.stage1 || [];
        setModels(s1);
        if (s1.length > 0) setSelectedModel(s1[0]);

        // Stage 2
        const s2 = data.stage2 || [];
        setStage2Models(s2);
        if (s2.length > 0) setSelectedStage2Model(s2[0]);

        // Stage 3
        const s3 = data.stage3 || [];
        setStage3Models(s3);
        if (s3.length > 0) setSelectedStage3Model(s3[0]);
      })
      .catch((err) => console.error("Failed to fetch models:", err));
    fetchSystemDevices()
      .then(setDevices)
      .catch((err) => console.error("Failed to fetch devices:", err));
  }, []);

  const [batchProgress, setBatchProgress] = useState<{ current: number; total: number } | null>(
    null,
  );

  const generateThumbnail = async (file: File): Promise<string> => {
    return new Promise((resolve) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        let w = img.width,
          h = img.height;
        if (w > h) {
          h = (h / w) * 160;
          w = 160;
        } else {
          w = (w / h) * 120;
          h = 120;
        }
        canvas.width = w;
        canvas.height = h;
        const ctx = canvas.getContext("2d");
        ctx?.drawImage(img, 0, 0, w, h);
        URL.revokeObjectURL(img.src);
        resolve(canvas.toDataURL("image/jpeg", 0.7));
      };
      img.src = URL.createObjectURL(file);
    });
  };

  const runBatch = async () => {
    if (!pendingFiles) return;
    setBatchProgress({ current: 0, total: pendingFiles.length });
    const items: any[] = [];
    const t_batch_start = performance.now();
    for (const file of pendingFiles) {
      try {
        const payload = await runInspection({
          file,
          modelName: selectedModel,
          stage2ModelName: selectedStage2Model || undefined,
          stage2Mode,
          stage2Preset: stage2Mode === "sahi" ? stage2Preset : undefined,
          stage2Conf: stage2Mode === "direct" ? stage2Conf : undefined,
          device,
          enableStage1,
          enableStage2,
          enableStage3,
        });
        const thumbnail = await generateThumbnail(file);
        items.push({
          file,
          objectUrl: URL.createObjectURL(file),
          thumbnail,
          payload,
        });
      } catch (err) {
        console.error(`Failed to inspect ${file.name}:`, err);
      }
      setBatchProgress((prev) => (prev ? { ...prev, current: prev.current + 1 } : null));
    }

    const totalMs = performance.now() - t_batch_start;
    setBatchProgress(null);

    if (items.length > 0) {
      onRunBatch(items, totalMs);
      toast.success(`Batch complete! ${items.length} images processed.`);
      // Auto-register as a batch on the backend
      try {
        const ids = items.map((i) => i.payload?.inspection_id).filter(Boolean);
        if (ids.length > 0) {
          await createBatch(ids);
        }
      } catch (err) {
        console.warn("Failed to register batch on backend:", err);
      }
    } else {
      toast.error("Batch failed. No images processed.");
    }
  };

  const handleFile = (e: ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    if (files.length === 1) {
      onImage(files[0]);
      toast.info(`Image loaded. Configure settings and click "Run Inspection".`);
    } else if (files.length > 1) {
      onSetPendingFiles(files);
      toast.info(`${files.length} images queued. Configure settings and click "Run Batch".`);
    }

    if (inputRef.current) inputRef.current.value = "";
  };

  const handleDrop = (e: DragEvent) => {
    e.preventDefault();
    const files = Array.from(e.dataTransfer.files || []).filter((f) => f.type.startsWith("image/"));
    if (files.length === 0) return;

    if (files.length === 1) {
      onImage(files[0]);
      toast.info(`Image loaded. Configure settings and click "Run Inspection".`);
    } else if (files.length > 1) {
      onSetPendingFiles(files);
      toast.info(`${files.length} images queued. Configure settings and click "Run Batch".`);
    }
  };

  const togglePanel = (id: PanelId) => {
    const next = new Set(filters.panels);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onFilters({ panels: next });
  };
  const toggleClass = (id: DefectClass) => {
    const next = new Set(filters.classes);
    if (next.has(id)) next.delete(id);
    else next.add(id);
    onFilters({ classes: next });
  };

  const exportJson = () => {
    if (!payload) return;
    const blob = new Blob([JSON.stringify(payload, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `inspection-${payload.timestamp}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const running = (stage !== "idle" && stage !== "done") || batchProgress !== null;
  const allStagesOff = !enableStage1 && !enableStage2 && !enableStage3;
  const disabledStages = payload?.disabled_stages ?? [
    ...(enableStage1 ? [] : ["stage1"]),
    ...(enableStage2 ? [] : ["stage2"]),
    ...(enableStage3 ? [] : ["stage3"]),
  ];

  return (
    <aside className="flex h-full flex-col gap-5 overflow-y-auto border-r border-border bg-sidebar/40 p-5">
      <div>
        <p className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Zone A · Controls
        </p>
        <h2 className="mt-1 text-sm font-semibold uppercase tracking-wide">Inspection Console</h2>
      </div>
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="rounded-sm border border-dashed border-border bg-card/40 p-4 text-center"
      >
        <Upload className="mx-auto h-5 w-5 text-muted-foreground" />
        <p className="mt-2 text-xs text-muted-foreground">Drop a high-res vehicle frame or</p>
        <Button
          variant="ghost"
          size="sm"
          className="mt-1 h-7 text-xs"
          onClick={() => inputRef.current?.click()}
        >
          Browse image
        </Button>
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          multiple
          className="hidden"
          onChange={handleFile}
        />
        {batchProgress ? (
          <div className="mt-3 space-y-1">
            <p className="text-[11px] font-medium text-foreground">
              Processing {batchProgress.current} / {batchProgress.total}...
            </p>
            <Progress
              value={(batchProgress.current / batchProgress.total) * 100}
              className="h-1.5"
            />
          </div>
        ) : pendingFiles && pendingFiles.length > 1 ? (
          <p className="mt-2 text-[11px] font-medium text-green-600 dark:text-green-400">
            ✓ {pendingFiles.length} images uploaded
          </p>
        ) : (
          imageName && <p className="mt-2 truncate text-[11px] text-foreground/70">{imageName}</p>
        )}
      </div>
      <Button
        variant="outline"
        size="sm"
        className="h-7 w-full text-xs"
        onClick={onOpenPastBatches}
        disabled={running}
      >
        <Download className="mr-1.5 h-3 w-3" /> Import past batch
      </Button>
      <div className="space-y-1.5">
        <p className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Stage 1 Model
        </p>
        <Select value={selectedModel} onValueChange={setSelectedModel}>
          <SelectTrigger className="h-8 text-xs">
            <SelectValue placeholder="Select a model" />
          </SelectTrigger>
          <SelectContent>
            {models.map((m) => (
              <SelectItem key={m} value={m} className="text-xs">
                {m}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1.5">
        <p className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Stage 2 Model
        </p>
        <Select
          value={selectedStage2Model}
          onValueChange={setSelectedStage2Model}
          disabled={stage2Models.length === 0}
        >
          <SelectTrigger className="h-8 text-xs">
            <SelectValue
              placeholder={stage2Models.length === 0 ? "No Stage 2 models" : "Select a model"}
            />
          </SelectTrigger>
          <SelectContent>
            {stage2Models.map((m) => (
              <SelectItem key={m} value={m} className="text-xs">
                {m}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1.5">
        <p className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Stage 2 Inference
        </p>
        <div className="grid grid-cols-2 gap-1 rounded-sm border border-border bg-card/40 p-1">
          <button
            type="button"
            onClick={() => setStage2Mode("direct")}
            className={cn(
              "rounded-sm px-1 py-1.5 text-center text-[10px] font-medium uppercase tracking-wide transition",
              stage2Mode === "direct"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:bg-accent hover:text-foreground",
            )}
          >
            <span className="block font-mono text-[9px] uppercase tracking-wider opacity-70">
              Fast
            </span>
          </button>

          <button
            type="button"
            onClick={() => setStage2Mode("sahi")}
            className={cn(
              "rounded-sm px-1 py-1.5 text-center text-[10px] font-medium uppercase tracking-wide transition",
              stage2Mode === "sahi"
                ? "bg-primary text-primary-foreground shadow-sm"
                : "text-muted-foreground hover:bg-accent hover:text-foreground",
            )}
          >
            <span className="block font-mono text-[9px] uppercase tracking-wider opacity-70">
              High-recall
            </span>
          </button>
        </div>
      </div>

      <div className="space-y-1.5" title="Presets apply to the SAHI pipeline">
        <p className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          SAHI Preset
        </p>
        <Select
          value={stage2Preset}
          onValueChange={(v) => setStage2Preset(v as typeof stage2Preset)}
          disabled={stage2Mode !== "sahi"}
        >
          <SelectTrigger className="h-8 text-xs">
            <SelectValue placeholder="Select preset" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="balanced" className="text-xs">
              Balanced
            </SelectItem>
            <SelectItem value="safety" className="text-xs">
              Safety
            </SelectItem>
            <SelectItem value="max_recall" className="text-xs">
              Max Recall
            </SelectItem>
          </SelectContent>
        </Select>
        {stage2Mode !== "sahi" && (
          <p className="text-[10px] text-muted-foreground">Presets apply to the SAHI pipeline.</p>
        )}
      </div>

      <div className="space-y-1.5" title="Direct confidence applies to Fast mode only">
        <div className="mb-1 flex items-center justify-between">
          <p className="font-mono text-[11px] font-medium uppercase tracking-wide">
            Direct Confidence
          </p>
          <Badge variant="secondary" className="h-5 text-[10px]">
            {Math.round(stage2Conf * 100)}%
          </Badge>
        </div>
        <Slider
          value={[stage2Conf * 100]}
          min={5}
          max={50}
          step={1}
          disabled={stage2Mode !== "direct"}
          onValueChange={(v) => setStage2Conf(v[0] / 100)}
        />
        {stage2Mode !== "direct" && (
          <p className="text-[10px] text-muted-foreground">
            Direct confidence applies to Fast mode only.
          </p>
        )}
      </div>

      <div className="space-y-1.5">
        <p className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Stage 3 Model
        </p>
        <Select
          value={selectedStage3Model}
          onValueChange={setSelectedStage3Model}
          disabled={stage3Models.length === 0}
        >
          <SelectTrigger className="h-8 text-xs">
            <SelectValue
              placeholder={stage3Models.length === 0 ? "No Stage 3 models" : "Select a model"}
            />
          </SelectTrigger>
          <SelectContent>
            {stage3Models.map((m) => (
              <SelectItem key={m} value={m} className="text-xs">
                {m}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>
      <div className="space-y-1.5">
        <p className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Compute Device
        </p>
        <Select value={device} onValueChange={setDevice}>
          <SelectTrigger className="h-8 text-xs">
            <SelectValue placeholder="Select device" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="auto" className="text-xs">
              Auto (Best Available)
            </SelectItem>
            <SelectItem value="cpu" className="text-xs">
              CPU
            </SelectItem>
            {devices?.mps && (
              <SelectItem value="mps" className="text-xs">
                MPS (Apple Silicon)
              </SelectItem>
            )}
            {devices?.cuda && (
              <SelectItem value="cuda:0" className="text-xs">
                CUDA ({devices.cuda_name || "GPU"})
              </SelectItem>
            )}
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-1.5">
        <p className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Pipeline stages
        </p>
        <div className="space-y-3 rounded-sm border border-border bg-card/40 p-3">
          <div className="flex items-center justify-between gap-3">
            <div className="space-y-0.5">
              <Label htmlFor="toggle-stage1" className="text-[11px] font-medium">
                Stage 1 — Anomaly screener
              </Label>
              <p className="text-[10px] leading-snug text-muted-foreground">
                Pre-screen; skips heavy processing on clean vehicles.
              </p>
            </div>
            <Switch
              id="toggle-stage1"
              checked={enableStage1}
              onCheckedChange={(v) => onStageToggles({ enableStage1: v })}
            />
          </div>
          <div className="flex items-center justify-between gap-3">
            <div className="space-y-0.5">
              <Label htmlFor="toggle-stage2" className="text-[11px] font-medium">
                Stage 2 — Defect classes
              </Label>
              <p className="text-[10px] leading-snug text-muted-foreground">
                Detects and classifies defects on image tiles.
              </p>
            </div>
            <Switch
              id="toggle-stage2"
              checked={enableStage2}
              onCheckedChange={(v) => onStageToggles({ enableStage2: v })}
            />
          </div>
          <div className="flex items-center justify-between gap-3">
            <div className="space-y-0.5">
              <Label htmlFor="toggle-stage3" className="text-[11px] font-medium">
                Stage 3 — Panel context
              </Label>
              <p className="text-[10px] leading-snug text-muted-foreground">
                Maps detections to vehicle panels for context.
              </p>
            </div>
            <Switch
              id="toggle-stage3"
              checked={enableStage3}
              onCheckedChange={(v) => onStageToggles({ enableStage3: v })}
            />
          </div>
        </div>
      </div>

      <div className="space-y-2">
        {pendingFiles ? (
          <>
            <Button
              className="w-full rounded-sm uppercase tracking-wide bg-primary"
              onClick={runBatch}
              disabled={running || allStagesOff}
            >
              <Play className="mr-2 h-4 w-4" />
              Run Batch ({pendingFiles.length} images)
            </Button>
            <p className="text-[10px] text-center text-muted-foreground">
              ↑ Click to start batch processing
            </p>
          </>
        ) : (
          <>
            <Button
              className="w-full rounded-sm uppercase tracking-wide"
              onClick={() =>
                onRun({
                  modelName: selectedModel,
                  stage2ModelName: selectedStage2Model || undefined,
                  stage2Mode,
                  stage2Preset: stage2Mode === "sahi" ? stage2Preset : undefined,
                  stage2Conf: stage2Mode === "direct" ? stage2Conf : undefined,
                  device,
                })
              }
              disabled={running || allStagesOff || !imageName}
            >
              <Play className="mr-2 h-4 w-4" />
              Run Inspection
            </Button>
            {!imageName && (
              <p className="text-[10px] text-center text-muted-foreground">Upload an image first</p>
            )}
            {imageName && !allStagesOff && (
              <p className="text-[10px] text-center text-muted-foreground">
                ↑ Click to start inspection
              </p>
            )}
          </>
        )}
        {allStagesOff && (
          <p className="text-[10px] text-center text-muted-foreground">Enable at least one stage</p>
        )}
        <div className="grid grid-cols-2 gap-2">
          <Button
            variant="outline"
            size="sm"
            className="rounded-sm"
            onClick={() => onRun({ forceClean: true })}
            disabled={running}
          >
            <ShieldCheck className="mr-1.5 h-3.5 w-3.5" />
            Simulate clean
          </Button>
          <Button variant="outline" size="sm" className="rounded-sm" onClick={onReset}>
            <RefreshCw className="mr-1.5 h-3.5 w-3.5" />
            Reset
          </Button>
        </div>
      </div>
      <div className="space-y-2">
        <StageStatus stage={stage} disabledStages={disabledStages} />
        <p className="text-[11px] leading-snug text-muted-foreground">{message}</p>
      </div>
      <div className="space-y-1.5">
        <p className="font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground">
          Stage layer view
        </p>
        <div className="grid grid-cols-3 gap-1 rounded-sm border border-border bg-card/40 p-1">
          {VIEW_STAGES.map((s) => (
            <button
              key={s.id}
              onClick={() => onViewStage?.(s.id)}
              className={cn(
                "rounded-sm px-1 py-1.5 text-center text-[10px] font-medium uppercase tracking-wide transition",
                viewStage === s.id
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "text-muted-foreground hover:bg-accent hover:text-foreground",
              )}
            >
              <span className="block font-mono text-[9px] uppercase tracking-wider opacity-70">
                S{s.id}
              </span>
              {s.label}
            </button>
          ))}
        </div>
      </div>
      <Separator />
      <section className="space-y-3">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          Filters
        </h3>

        <div>
          <p className="mb-1.5 text-[11px] font-medium">Panels</p>
          <div className="flex flex-wrap gap-1">
            {ALL_PANELS.map((p) => {
              const active = filters.panels.has(p);
              return (
                <button
                  key={p}
                  onClick={() => togglePanel(p)}
                  className={cn(
                    "rounded-sm border px-2 py-0.5 font-mono text-[10px] uppercase transition",
                    active
                      ? "border-primary bg-primary text-primary-foreground"
                      : "border-border text-muted-foreground hover:bg-accent",
                  )}
                >
                  {PANEL_LABELS[p]}
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <p className="mb-1.5 text-[11px] font-medium">Defect classes</p>
          <div className="flex flex-wrap gap-1">
            {DEFECT_CLASSES.map((c) => {
              const active = filters.classes.has(c.id);
              return (
                <button
                  key={c.id}
                  onClick={() => toggleClass(c.id)}
                  className={cn(
                    "flex items-center gap-1 rounded-sm border px-2 py-0.5 font-mono text-[10px] uppercase transition",
                    active
                      ? "border-foreground/60 bg-foreground/10"
                      : "border-border text-muted-foreground hover:bg-accent",
                  )}
                >
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: c.color }} />
                  {c.label}
                </button>
              );
            })}
          </div>
        </div>

        <div>
          <div className="mb-1 flex items-center justify-between">
            <p className="font-mono text-[11px] font-medium uppercase tracking-wide">
              Min confidence
            </p>
            <Badge variant="secondary" className="h-5 text-[10px]">
              {Math.round(filters.minConfidence * 100)}%
            </Badge>
          </div>
          <Slider
            value={[filters.minConfidence * 100]}
            max={100}
            step={1}
            onValueChange={(v) => onFilters({ minConfidence: v[0] / 100 })}
          />
        </div>

        <div>
          <div className="mb-1 flex items-center justify-between">
            <p className="font-mono text-[11px] font-medium uppercase tracking-wide">Min DSI</p>
            <Badge variant="secondary" className="h-5 text-[10px]">
              {(filters.minDsi * 100).toFixed(2)}%
            </Badge>
          </div>
          <Slider
            value={[filters.minDsi * 1000]}
            max={20}
            step={0.1}
            onValueChange={(v) => onFilters({ minDsi: v[0] / 1000 })}
          />
        </div>
      </section>
      <Separator />
      <Button
        variant="outline"
        size="sm"
        className="rounded-sm font-mono uppercase tracking-wide"
        onClick={exportJson}
        disabled={!payload}
      >
        <Download className="mr-1.5 h-3.5 w-3.5" />
        Export JSON
      </Button>
      <SystemMetricsPanel />
    </aside>
  );
}
