import type { ModelVersion, ModelStage } from "@/lib/inspection/modelRegistrySchema";
import { ModelTrackCard } from "./ModelTrackCard";
import { EmptyState } from "@/components/Shared";

interface Props {
  stage: ModelStage;
  stageLabel: string;
  models: ModelVersion[];
}

const STATUS_ORDER: Record<string, number> = {
  deployed: 0,
  champion: 1,
  candidate: 2,
  rejected: 3,
  archived: 4,
};

export function ModelTrackLane({ stage, stageLabel, models }: Props) {
  const sorted = [...models].sort((a, b) => {
    const ao = STATUS_ORDER[a.status] ?? 9;
    const bo = STATUS_ORDER[b.status] ?? 9;
    if (ao !== bo) return ao - bo;
    return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
  });
  return (
    <div className="rounded-lg border border-border bg-background p-4">
      <div className="mb-3 flex items-center gap-2">
        <span className="font-mono text-[10px] font-semibold uppercase tracking-widest text-primary">
          {stage}
        </span>
        <h3 className="text-sm font-semibold">{stageLabel}</h3>
        <span className="ml-auto font-mono text-[10px] text-muted-foreground">
          {models.length} model{models.length === 1 ? "" : "s"}
        </span>
      </div>
      {sorted.length === 0 ? (
        <EmptyState
          title={`No models for ${stageLabel}`}
          hint="Train a model to populate this track."
        />
      ) : (
        <div className="flex gap-3 overflow-x-auto pb-2">
          {sorted.map((m) => (
            <ModelTrackCard key={m.id} model={m} />
          ))}
        </div>
      )}
    </div>
  );
}
