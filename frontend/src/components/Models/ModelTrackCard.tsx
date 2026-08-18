import type { ModelVersion } from "@/lib/inspection/modelRegistrySchema";
import { STATUS_TONE_MAP, getPrimaryMetric, formatDate } from "./modelUtils";
import { StatusBadge } from "@/components/Shared";
import { Crown, Rocket } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  model: ModelVersion;
}

export function ModelTrackCard({ model }: Props) {
  const metric = getPrimaryMetric(model.metrics, model.stage);
  const isChampion = model.status === "champion";
  const isDeployed = model.status === "deployed";
  return (
    <div
      className={cn(
        "w-44 shrink-0 rounded-md border border-border bg-card p-3",
        isChampion && "border-status-pass/50 bg-status-pass/5",
        isDeployed && "border-primary/50 bg-primary/5",
      )}
    >
      <div className="flex items-center justify-between gap-1">
        <p className="truncate font-mono text-[10px] text-muted-foreground">v{model.version}</p>
        {isDeployed ? (
          <Rocket className="h-3.5 w-3.5 shrink-0 text-primary" />
        ) : isChampion ? (
          <Crown className="h-3.5 w-3.5 shrink-0 text-status-pass" />
        ) : null}
      </div>
      <p className="mt-1 truncate text-xs font-medium" title={model.model_name}>
        {model.model_name}
      </p>
      <div className="mt-2">
        <StatusBadge tone={STATUS_TONE_MAP[model.status]}>{model.status}</StatusBadge>
      </div>
      <div className="mt-2 flex items-center justify-between font-mono text-[10px] text-muted-foreground">
        <span>{metric.key}</span>
        <span className="text-foreground">{metric.value}</span>
      </div>
      <p className="mt-1 font-mono text-[9px] text-muted-foreground/70">
        {formatDate(model.created_at)}
      </p>
    </div>
  );
}
