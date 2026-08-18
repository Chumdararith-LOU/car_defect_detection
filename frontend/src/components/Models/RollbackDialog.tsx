import type { ModelVersion } from "@/lib/inspection/modelRegistrySchema";
import { STAGE_LABEL_MAP } from "./modelUtils";
import { Button } from "@/components/ui/button";

interface Props {
  model: ModelVersion | null;
  isLoading: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export function RollbackDialog({ model, isLoading, onConfirm, onClose }: Props) {
  if (!model) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="w-full max-w-md rounded-lg border bg-background p-6 shadow-lg">
        <h2 className="text-lg font-semibold">Rollback Model</h2>
        <p className="mt-2 text-sm text-muted-foreground">
          This will revert the production model for{" "}
          <span className="font-medium text-foreground">{STAGE_LABEL_MAP[model.stage]}</span>{" "}
          to the previously deployed version.
        </p>

        <div className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3">
          <p className="text-sm text-red-800">
            ⚠️ The current deployed model ({model.model_name} v{model.version}) will be
            archived and replaced by the previous version.
          </p>
        </div>

        <div className="mt-6 flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button
            size="sm"
            variant="destructive"
            onClick={onConfirm}
            disabled={isLoading}
          >
            {isLoading ? "Rolling back..." : "Confirm Rollback"}
          </Button>
        </div>
      </div>
    </div>
  );
}
