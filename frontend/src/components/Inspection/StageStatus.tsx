import type { PipelineStage } from "@/lib/inspection/schema";
import { Check, Loader2, Circle, Ban } from "lucide-react";
import { cn } from "@/lib/utils";

const STAGES: {
  key: Exclude<PipelineStage, "idle" | "done">;
  stageId: string;
  label: string;
}[] = [
  { key: "prescreen", stageId: "stage1", label: "Stage 1 · Binary Pre-Screen (SOD)" },
  { key: "tiling", stageId: "stage2", label: "Stage 2 · Tiled Instance Segmentation" },
  { key: "context", stageId: "stage3", label: "Stage 3 · Component Context Mapping" },
];

const order: PipelineStage[] = ["idle", "prescreen", "tiling", "context", "done"];

export function StageStatus({
  stage,
  disabledStages,
}: {
  stage: PipelineStage;
  disabledStages?: string[];
}) {
  const currentIdx = order.indexOf(stage);
  return (
    <ol className="space-y-2">
      {STAGES.map((s) => {
        const disabled = disabledStages?.includes(s.stageId) ?? false;
        const idx = order.indexOf(s.key);
        const done = !disabled && (currentIdx > idx || stage === "done");
        const active = !disabled && stage === s.key;
        return (
          <li
            key={s.key}
            className={cn(
              "flex items-start gap-3 rounded-md border border-border/60 px-3 py-2 text-xs",
              active && "border-primary/60 bg-primary/5",
              done && "text-muted-foreground",
              disabled && "border-border/40 text-muted-foreground/60",
            )}
          >
            <span className="mt-0.5">
              {disabled ? (
                <Ban className="h-3.5 w-3.5 text-muted-foreground/50" />
              ) : done ? (
                <Check className="h-3.5 w-3.5 text-status-pass" />
              ) : active ? (
                <Loader2 className="h-3.5 w-3.5 animate-spin text-primary" />
              ) : (
                <Circle className="h-3.5 w-3.5 text-muted-foreground/50" />
              )}
            </span>
            <span className="leading-snug">{s.label}</span>
            {disabled && (
              <span className="ml-auto shrink-0 rounded-sm border border-border/60 bg-muted/40 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-muted-foreground/70">
                Disabled
              </span>
            )}
          </li>
        );
      })}
    </ol>
  );
}
