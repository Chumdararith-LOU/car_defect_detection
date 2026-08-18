import { useEffect, useState } from "react";
import { Scissors, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { CheckpointPicker, TaxonomyPicker } from "@/components/Platform";
import { getSurgeryStatus, startSurgery } from "@/lib/inspection/apiClient";
import type { HeadInitMode } from "@/lib/inspection/platformSchema";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCompleted?: () => void;
}

type Phase = "idle" | "running" | "done" | "failed";

export function HeadSurgeryDialog({ open, onOpenChange, onCompleted }: Props) {
  const [sourceId, setSourceId] = useState<string | null>(null);
  const [taxonomyId, setTaxonomyId] = useState<string | null>(null);
  const [initMode, setInitMode] = useState<HeadInitMode>("fresh");
  const [phase, setPhase] = useState<Phase>("idle");
  const [jobId, setJobId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [outputId, setOutputId] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setSourceId(null);
      setTaxonomyId(null);
      setInitMode("fresh");
      setPhase("idle");
      setJobId(null);
      setError(null);
      setOutputId(null);
    }
  }, [open]);

  useEffect(() => {
    if (!jobId || phase !== "running") return;
    let cancelled = false;
    const timer = setInterval(async () => {
      try {
        const st = await getSurgeryStatus(jobId);
        if (cancelled) return;
        if (st.status === "completed") {
          setPhase("done");
          setOutputId(st.output_checkpoint_id);
          toast.success("Head surgery completed");
          onCompleted?.();
        } else if (st.status === "failed") {
          setPhase("failed");
          setError(st.error_message ?? "Surgery failed");
          toast.error("Head surgery failed");
        }
      } catch {
        // transient poll error — keep polling
      }
    }, 2000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [jobId, phase, onCompleted]);

  const canSubmit = sourceId != null && taxonomyId != null && phase !== "running";

  async function handleSubmit() {
    if (!sourceId || !taxonomyId) return;
    setPhase("running");
    setError(null);
    try {
      const res = await startSurgery({
        source_checkpoint_id: sourceId,
        taxonomy_id: taxonomyId,
        head_init_mode: initMode,
      });
      setJobId(res.job_id);
    } catch (e) {
      setPhase("failed");
      setError(e instanceof Error ? e.message : "Failed to start surgery");
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Head Surgery</DialogTitle>
          <DialogDescription>
            Remap a checkpoint head to a target taxonomy. Backbone weights are transferred;
            mismatched head tensors are re-initialized.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-4">
          <div className="space-y-2">
            <Label>Source checkpoint</Label>
            <CheckpointPicker value={sourceId} onChange={setSourceId} />
          </div>
          <div className="space-y-2">
            <Label>Target taxonomy</Label>
            <TaxonomyPicker value={taxonomyId} onChange={setTaxonomyId} />
          </div>
          <div className="space-y-2">
            <Label>Head init mode</Label>
            <RadioGroup
              value={initMode}
              onValueChange={(v) => setInitMode(v as HeadInitMode)}
              className="space-y-2"
            >
              <div className="flex items-start gap-2">
                <RadioGroupItem value="fresh" id="init-fresh" />
                <Label htmlFor="init-fresh" className="font-normal">
                  Fresh head init (recommended) — keep new random head weights
                </Label>
              </div>
              <div className="flex items-start gap-2">
                <RadioGroupItem value="class_aware" id="init-aware" />
                <Label htmlFor="init-aware" className="font-normal">
                  Class-aware copy — copy overlapping class rows from source head
                </Label>
              </div>
            </RadioGroup>
          </div>
          {phase === "running" && (
            <p className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Running surgery…
            </p>
          )}
          {phase === "done" && (
            <p className="text-xs text-status-pass">
              Done. New checkpoint registered
              {outputId ? ` (${outputId.slice(0, 8)}…)` : ""}.
            </p>
          )}
          {phase === "failed" && error && <p className="text-xs text-status-fail">{error}</p>}
        </div>
        <DialogFooter>
          <Button variant="outline" size="sm" onClick={() => onOpenChange(false)}>
            Close
          </Button>
          <Button size="sm" disabled={!canSubmit} onClick={handleSubmit}>
            {phase === "running" ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Scissors className="h-4 w-4" />
            )}
            Run surgery
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
