import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, Shuffle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { ResplitResponse } from "@/lib/inspection/prepSchema";
import { resplitDataset } from "@/lib/inspection/apiClient";
import { SplitStructurePanel } from "./SplitStructurePanel";

interface Props {
  datasetId: string;
  totalImages: number;
  onClose: () => void;
  onComplete: () => void;
}

interface RatioPreset {
  label: string;
  train: number;
  val: number;
  test: number;
}

const RATIO_PRESETS: RatioPreset[] = [
  { label: "80 / 20", train: 0.8, val: 0.2, test: 0.0 },
  { label: "80 / 10 / 10", train: 0.8, val: 0.1, test: 0.1 },
  { label: "70 / 20 / 10", train: 0.7, val: 0.2, test: 0.1 },
  { label: "70 / 15 / 15", train: 0.7, val: 0.15, test: 0.15 },
];

export function ResplitDialog({ datasetId, totalImages, onClose, onComplete }: Props) {
  const [trainRatio, setTrainRatio] = useState(0.8);
  const [valRatio, setValRatio] = useState(0.1);
  const [testRatio, setTestRatio] = useState(0.1);
  const [seed, setSeed] = useState(42);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<ResplitResponse | null>(null);

  const sum = trainRatio + valRatio + testRatio;
  const sumIsValid = Math.abs(sum - 1.0) < 0.001;

  const ratioFields = [
    { label: "Train", value: trainRatio, setter: setTrainRatio },
    { label: "Val", value: valRatio, setter: setValRatio },
    { label: "Test", value: testRatio, setter: setTestRatio },
  ];

  const applyPreset = (preset: RatioPreset) => {
    setTrainRatio(preset.train);
    setValRatio(preset.val);
    setTestRatio(preset.test);
    setError(null);
  };

  const handleResplit = async () => {
    if (!sumIsValid) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await resplitDataset(datasetId, {
        train_ratio: trainRatio,
        val_ratio: valRatio,
        test_ratio: testRatio,
        seed,
      });
      setResult(res);
      onComplete();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to re-split dataset");
    } finally {
      setSubmitting(false);
    }
  };

  // ---- Phase 2: result ----
  if (result) {
    return (
      <Dialog
        open
        onOpenChange={(o) => {
          if (!o) onClose();
        }}
      >
        <DialogContent className="max-w-lg space-y-4">
          <DialogHeader>
            <DialogTitle>Re-split Complete</DialogTitle>
            <DialogDescription>{result.message}</DialogDescription>
          </DialogHeader>
          <SplitStructurePanel structure={result.new_structure} />
          <DialogFooter>
            <Button onClick={onClose}>Done</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    );
  }

  // ---- Phase 1: form ----
  return (
    <Dialog
      open
      onOpenChange={(o) => {
        if (!o) onClose();
      }}
    >
      <DialogContent className="max-w-md space-y-4">
        <DialogHeader>
          <DialogTitle>Re-split Dataset</DialogTitle>
          <DialogDescription>Choose train / val / test ratios and a seed.</DialogDescription>
        </DialogHeader>

        {/* Presets */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Presets</label>
          <div className="flex flex-wrap gap-2">
            {RATIO_PRESETS.map((preset) => (
              <button
                key={preset.label}
                onClick={() => applyPreset(preset)}
                className="rounded-md border border-border bg-muted/30 px-2.5 py-1.5 text-xs transition-colors hover:bg-muted"
              >
                {preset.label}
              </button>
            ))}
          </div>
        </div>

        {/* Ratio inputs */}
        <div className="grid grid-cols-3 gap-2">
          {ratioFields.map((field) => (
            <div key={field.label} className="space-y-1.5">
              <label className="text-xs font-medium text-muted-foreground">{field.label}</label>
              <input
                type="number"
                min={0}
                max={1}
                step={0.05}
                value={field.value}
                onChange={(e) => field.setter(Number(e.target.value))}
                className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
          ))}
        </div>

        {/* Seed */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Seed</label>
          <input
            type="number"
            value={seed}
            onChange={(e) => setSeed(Number(e.target.value))}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
          <p className="text-[11px] text-muted-foreground">Same seed = same split every time.</p>
        </div>

        {/* Live preview */}
        <div className="rounded-md border border-border bg-muted/30 p-3 text-xs">
          <p className="mb-1 text-muted-foreground">
            Splitting <span className="font-semibold">{totalImages.toLocaleString()}</span> images
          </p>
          <div className="grid grid-cols-3 gap-2 text-center">
            {ratioFields.map((field) => (
              <div key={field.label}>
                <p className="text-muted-foreground">{field.label}</p>
                <p className="font-semibold">
                  {Math.round(totalImages * field.value).toLocaleString()}
                </p>
              </div>
            ))}
          </div>
        </div>

        {!sumIsValid && (
          <p className="text-xs text-destructive">
            Ratios must sum to 1.0 (current sum: {sum.toFixed(2)})
          </p>
        )}

        {error && <p className="text-xs text-destructive">{error}</p>}

        <DialogFooter>
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={handleResplit} disabled={!sumIsValid || submitting}>
            {submitting ? (
              <>
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> Re-splitting...
              </>
            ) : (
              <>
                <Shuffle className="mr-1.5 h-4 w-4" /> Re-split Dataset
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
