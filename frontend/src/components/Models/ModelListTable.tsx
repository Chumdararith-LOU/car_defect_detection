import type { ModelVersion } from "@/lib/inspection/modelRegistrySchema";
import {
  STATUS_TONE_MAP,
  STAGE_LABEL_MAP,
  getPrimaryMetric,
  formatDate,
  shortDatasetName,
} from "./modelUtils";
import { EmptyState, StatusBadge } from "@/components/Shared";
interface Props {
  models: ModelVersion[];
  selectedId: string | null;
  onSelect: (model: ModelVersion) => void;
}

export function ModelListTable({ models, selectedId, onSelect }: Props) {
  if (models.length === 0) {
    return (
      <EmptyState
        title="No models registered yet"
        hint="Launch a training job to create candidates."
      />
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border">
      <table className="w-full table-fixed text-sm">
        <thead>
          <tr className="border-b bg-muted/50">
            <th className="w-[110px] px-3 py-3 text-left font-medium">Stage</th>
            <th className="w-[20%] px-3 py-3 text-left font-medium">Name</th>
            <th className="w-[15%] px-3 py-3 text-left font-medium">Version</th>
            <th className="px-3 py-3 text-left font-medium">Dataset</th>
            <th className="w-[110px] px-3 py-3 text-left font-medium">Metric</th>
            <th className="w-[95px] px-3 py-3 text-left font-medium">Status</th>
            <th className="w-[150px] px-3 py-3 text-left font-medium">Created</th>
          </tr>
        </thead>
        <tbody>
          {models.map((model) => {
            const metric = getPrimaryMetric(model.metrics, model.stage);
            const isSelected = model.id === selectedId;
            return (
              <tr
                key={model.id}
                onClick={() => onSelect(model)}
                className={`cursor-pointer border-b transition-colors hover:bg-muted/50 ${
                  isSelected ? "bg-primary/5" : ""
                }`}
              >
                <td className="truncate px-3 py-3" title={STAGE_LABEL_MAP[model.stage]}>
                  {STAGE_LABEL_MAP[model.stage]}
                </td>
                <td className="truncate px-3 py-3 font-medium" title={model.model_name}>
                  {model.model_name}
                </td>
                <td className="truncate px-3 py-3 font-mono text-xs" title={model.version}>
                  {model.version}
                </td>
                <td
                  className="truncate px-3 py-3 text-muted-foreground"
                  title={model.dataset_version || undefined}
                >
                  {shortDatasetName(model.dataset_version)}
                </td>
                <td className="truncate px-3 py-3">
                  <span className="text-muted-foreground">{metric.key}: </span>
                  <span className="font-medium">{metric.value}</span>
                </td>
                <td className="px-3 py-3">
                  <StatusBadge tone={STATUS_TONE_MAP[model.status]} size="md">
                    {model.status}
                  </StatusBadge>
                </td>
                <td className="truncate px-3 py-3 text-muted-foreground">
                  {formatDate(model.created_at)}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
