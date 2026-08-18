import type { ModelVersion } from "@/lib/inspection/modelRegistrySchema";
import { STAGE_LABEL_MAP } from "./modelUtils";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface Props {
  model: ModelVersion | null;
  isLoading: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export function DeployDialog({ model, isLoading, onConfirm, onClose }: Props) {
  if (!model) return null;

  return (
    <Dialog
      open
      onOpenChange={(o) => {
        if (!o) onClose();
      }}
    >
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Deploy to Production</DialogTitle>
          <DialogDescription>
            This will update the active model symlink for{" "}
            <span className="font-medium text-foreground">{STAGE_LABEL_MAP[model.stage]}</span>.
          </DialogDescription>
        </DialogHeader>

        <div className="mt-4 rounded-lg border border-yellow-200 bg-yellow-50 p-3">
          <p className="text-sm text-yellow-800">
            The inspection pipeline will immediately start using this model for new inspections.
            Ensure it has been validated against your test cases.
          </p>
        </div>

        <div className="mt-4 rounded-lg border p-3">
          <p className="text-xs text-muted-foreground">Model</p>
          <p className="text-sm font-medium">
            {model.model_name} v{model.version}
          </p>
          <p className="text-xs text-muted-foreground">Dataset</p>
          <p className="text-sm">{model.dataset_version || "—"}</p>
        </div>

        <DialogFooter>
          <Button variant="outline" size="sm" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button size="sm" onClick={onConfirm} disabled={isLoading}>
            {isLoading ? "Deploying..." : "Confirm Deployment"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
