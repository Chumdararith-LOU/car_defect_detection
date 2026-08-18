import type { ModelVersion } from "@/lib/inspection/modelRegistrySchema";
import {
  STATUS_TONE_MAP,
  STAGE_LABEL_MAP,
  formatMetricValue,
  formatDate,
  shortDatasetName,
} from "./modelUtils";
import { StatusBadge } from "@/components/Shared";
import { Button } from "@/components/ui/button";

interface Props {
  model: ModelVersion | null;
  onPromote: (model: ModelVersion) => void;
  onDeploy: (model: ModelVersion) => void;
  onRollback: (model: ModelVersion) => void;
}

export function ModelDetailPanel({ model, onPromote, onDeploy, onRollback }: Props) {
  if (!model) {
    return (
      <div className="flex h-full items-center justify-center text-muted-foreground">
        Select a model to view details
      </div>
    );
  }

  const metricEntries = Object.entries(model.metrics);
  const gateEntries = model.evaluation_report?.gates as
    | Array<{
        gate_name: string;
        passed: boolean;
        reason: string;
      }>
    | undefined;

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="space-y-2">
        <div className="flex items-center gap-3">
          <h2 className="break-all text-xl font-semibold">{model.model_name}</h2>
          <StatusBadge tone={STATUS_TONE_MAP[model.status]} size="md">
            {model.status}
          </StatusBadge>
        </div>
        <p className="text-sm text-muted-foreground">
          {STAGE_LABEL_MAP[model.stage]} · v{model.version}
        </p>
      </div>

      {/* Metadata */}
      <div className="grid grid-cols-2 gap-4 rounded-lg border p-4">
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">Dataset</p>
          <p className="text-sm font-medium">{shortDatasetName(model.dataset_version)}</p>
          {model.dataset_version && (
            <p className="break-all text-xs text-muted-foreground">{model.dataset_version}</p>
          )}
        </div>
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">Training Run</p>
          <p className="break-all font-mono text-xs">{model.training_run_id || "—"}</p>
        </div>
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">Created</p>
          <p className="text-sm">{formatDate(model.created_at)}</p>
        </div>
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">Promoted</p>
          <p className="text-sm">{formatDate(model.promoted_at)}</p>
        </div>
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">Deployed</p>
          <p className="text-sm">{formatDate(model.deployed_at)}</p>
        </div>
        <div className="min-w-0">
          <p className="text-xs text-muted-foreground">Config Hash</p>
          <p className="break-all font-mono text-xs">{model.config_hash || "—"}</p>
        </div>
      </div>

      {/* Metrics */}
      {metricEntries.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium">Metrics</h3>
          <div className="grid grid-cols-2 gap-2 rounded-lg border p-4">
            {metricEntries.map(([key, value]) => (
              <div key={key}>
                <p className="text-xs text-muted-foreground">{key}</p>
                <p className="text-sm font-medium">{formatMetricValue(value)}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Evaluation Gates */}
      {gateEntries && gateEntries.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium">Evaluation Gates</h3>
          <div className="space-y-1 rounded-lg border p-4">
            {gateEntries.map((gate) => (
              <div key={gate.gate_name} className="flex items-center gap-2 text-sm">
                <span className={gate.passed ? "text-green-600" : "text-red-600"}>
                  {gate.passed ? "✓" : "✗"}
                </span>
                <span className="font-medium">{gate.gate_name}</span>
                <span className="text-muted-foreground">{gate.reason}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2 border-t pt-4">
        {model.status === "candidate" && (
          <Button onClick={() => onPromote(model)} variant="default" size="sm">
            Promote to Champion
          </Button>
        )}
        {model.status === "champion" && (
          <Button onClick={() => onDeploy(model)} variant="default" size="sm">
            Deploy to Production
          </Button>
        )}
        {model.status === "deployed" && (
          <Button onClick={() => onRollback(model)} variant="outline" size="sm">
            Rollback
          </Button>
        )}
      </div>
    </div>
  );
}
