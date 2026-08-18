import type { ModelVersion, GateResult } from "@/lib/inspection/modelRegistrySchema";
import { STAGE_LABEL_MAP, formatMetricValue } from "./modelUtils";
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
  candidate: ModelVersion | null;
  champion: ModelVersion | null;
  gateResults: GateResult[] | null;
  isLoading: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export function PromoteDialog({
  candidate,
  champion,
  gateResults,
  isLoading,
  onConfirm,
  onClose,
}: Props) {
  if (!candidate) return null;

  const allPassed = gateResults ? gateResults.every((g) => g.passed) : true;

  return (
    <Dialog
      open
      onOpenChange={(o) => {
        if (!o) onClose();
      }}
    >
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Promote to Champion</DialogTitle>
          <DialogDescription>
            {STAGE_LABEL_MAP[candidate.stage]} · {candidate.model_name} v{candidate.version}
          </DialogDescription>
        </DialogHeader>

        {/* Candidate vs Champion comparison */}
        <div className="mt-4 grid grid-cols-2 gap-4">
          <div className="rounded-lg border p-3">
            <p className="text-xs text-muted-foreground">Candidate</p>
            <p className="text-sm font-medium">{candidate.model_name}</p>
            <div className="mt-2 space-y-1">
              {Object.entries(candidate.metrics)
                .slice(0, 4)
                .map(([key, value]) => (
                  <p key={key} className="text-xs">
                    <span className="text-muted-foreground">{key}: </span>
                    <span className="font-medium">{formatMetricValue(value)}</span>
                  </p>
                ))}
            </div>
          </div>
          <div className="rounded-lg border p-3">
            <p className="text-xs text-muted-foreground">Current Champion</p>
            {champion ? (
              <>
                <p className="text-sm font-medium">{champion.model_name}</p>
                <div className="mt-2 space-y-1">
                  {Object.entries(champion.metrics)
                    .slice(0, 4)
                    .map(([key, value]) => (
                      <p key={key} className="text-xs">
                        <span className="text-muted-foreground">{key}: </span>
                        <span className="font-medium">{formatMetricValue(value)}</span>
                      </p>
                    ))}
                </div>
              </>
            ) : (
              <p className="mt-2 text-xs text-muted-foreground">No champion exists yet</p>
            )}
          </div>
        </div>

        {/* Gate results */}
        {gateResults && gateResults.length > 0 && (
          <div className="mt-4 space-y-1 rounded-lg border p-3">
            <p className="text-xs font-medium text-muted-foreground">Evaluation Gates</p>
            {gateResults.map((gate) => (
              <div key={gate.gate_name} className="flex items-center gap-2 text-sm">
                <span className={gate.passed ? "text-green-600" : "text-red-600"}>
                  {gate.passed ? "✓" : "✗"}
                </span>
                <span>{gate.gate_name}</span>
                <span className="ml-auto text-xs text-muted-foreground">{gate.reason}</span>
              </div>
            ))}
          </div>
        )}

        <DialogFooter>
          <Button variant="outline" size="sm" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button size="sm" onClick={onConfirm} disabled={isLoading || !allPassed}>
            {isLoading ? "Promoting..." : "Confirm Promotion"}
          </Button>
        </DialogFooter>
        {!allPassed && (
          <p className="text-xs text-red-600">
            Promotion blocked: one or more evaluation gates failed.
          </p>
        )}
      </DialogContent>
    </Dialog>
  );
}
