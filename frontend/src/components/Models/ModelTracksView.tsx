import { useEffect, useState } from "react";
import { fetchModelRegistryModels } from "@/lib/inspection/apiClient";
import type { ModelVersion, ModelStage } from "@/lib/inspection/modelRegistrySchema";
import { ModelTrackLane } from "./ModelTrackLane";
import { STAGE_LABEL_MAP } from "./modelUtils";
import { Loader2 } from "lucide-react";
import { EmptyState } from "@/components/Shared";

const TRACK_STAGES: ModelStage[] = ["stage1", "stage2", "stage3"];

export function ModelTracksView() {
  const [models, setModels] = useState<ModelVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchModelRegistryModels()
      .then((res) => {
        if (!cancelled) setModels(res.models);
      })
      .catch((e) => {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to load models");
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center p-12 text-muted-foreground">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading model tracks...
      </div>
    );
  }
  if (error) return <EmptyState title="Failed to load models" hint={error} />;

  return (
    <div className="space-y-4">
      {TRACK_STAGES.map((stage) => (
        <ModelTrackLane
          key={stage}
          stage={stage}
          stageLabel={STAGE_LABEL_MAP[stage]}
          models={models.filter((m) => m.stage === stage)}
        />
      ))}
    </div>
  );
}
