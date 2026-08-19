import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Hammer, Loader2, ArrowLeft } from "lucide-react";
import type { ReviewItem, DatasetStage, DatasetBuildResponse } from "@/lib/inspection/schema";
import { fetchAllReviews, buildDataset } from "@/lib/inspection/apiClient";

interface Props {
  onBack: () => void;
}

export function ReviewToDatasetBuilder({ onBack }: Props) {
  const [reviews, setReviews] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Build form state
  const [stage, setStage] = useState<DatasetStage>("stage2");
  const [versionName, setVersionName] = useState("");
  const [includeConfirmed, setIncludeConfirmed] = useState(true);
  const [includeRejected, setIncludeRejected] = useState(false);
  const [includeUnclear, setIncludeUnclear] = useState(false);
  const [notes, setNotes] = useState("");
  const [building, setBuilding] = useState(false);
  const [result, setResult] = useState<DatasetBuildResponse | null>(null);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const data = await fetchAllReviews();
        setReviews(data);
      } catch (err: any) {
        setError(err.message || "Failed to load reviews");
      } finally {
        setLoading(false);
      }
    };
    load();
  }, []);

  const counts = {
    confirm: reviews.filter((r) => r.operator_decision === "confirm").length,
    reject: reviews.filter((r) => r.operator_decision === "reject").length,
    reclassify: reviews.filter((r) => r.operator_decision === "reclassify").length,
    unclear: reviews.filter((r) => r.operator_decision === "unclear").length,
  };

  const confirmedPlusReclass = counts.confirm + counts.reclassify;
  const totalSelected =
    (includeConfirmed ? confirmedPlusReclass : 0) +
    (includeRejected ? counts.reject : 0) +
    (includeUnclear ? counts.unclear : 0);
  const onlyNegatives = totalSelected > 0 && confirmedPlusReclass === 0 && counts.unclear === 0;

  const canBuild = versionName.trim().length > 0 && totalSelected > 0;

  const handleBuild = async () => {
    setBuilding(true);
    setError(null);
    setResult(null);
    try {
      const res = await buildDataset({
        stage,
        version_name: versionName.trim(),
        include_confirmed: includeConfirmed,
        include_rejected: includeRejected,
        include_unclear: includeUnclear,
        notes: notes.trim() || null,
      });
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Build failed");
    } finally {
      setBuilding(false);
    }
  };

  if (loading) {
    return (
      <div className="rounded-lg border border-border bg-card p-8 text-center text-muted-foreground">
        Loading reviews...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <button
        onClick={onBack}
        className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
      >
        <ArrowLeft className="h-3.5 w-3.5" /> Back to dataset list
      </button>

      <div className="rounded-lg border border-border bg-card p-6 space-y-6">
        <div className="flex items-center gap-2">
          <Hammer className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold">Build Dataset from Review Flywheel</h2>
        </div>

        {/* Review counts */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          <div className="rounded-md border border-green-500/30 bg-green-500/10 p-3 text-center">
            <p className="text-2xl font-bold text-green-600 dark:text-green-400">
              {counts.confirm}
            </p>
            <p className="text-xs text-muted-foreground">Confirmed</p>
          </div>
          <div className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-center">
            <p className="text-2xl font-bold text-red-600 dark:text-red-400">{counts.reject}</p>
            <p className="text-xs text-muted-foreground">Rejected</p>
          </div>
          <div className="rounded-md border border-blue-500/30 bg-blue-500/10 p-3 text-center">
            <p className="text-2xl font-bold text-blue-600 dark:text-blue-400">
              {counts.reclassify}
            </p>
            <p className="text-xs text-muted-foreground">Reclassified</p>
          </div>
          <div className="rounded-md border border-yellow-500/30 bg-yellow-500/10 p-3 text-center">
            <p className="text-2xl font-bold text-yellow-600 dark:text-yellow-400">
              {counts.unclear}
            </p>
            <p className="text-xs text-muted-foreground">Unclear</p>
          </div>
        </div>

        {/* Include checkboxes */}
        <div className="space-y-2">
          <p className="text-sm font-medium">Include in dataset:</p>
          <div className="flex flex-wrap gap-4">
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={includeConfirmed}
                onChange={(e) => setIncludeConfirmed(e.target.checked)}
                className="rounded border-gray-300"
              />
              Confirmed + Reclassified ({confirmedPlusReclass})
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={includeRejected}
                onChange={(e) => setIncludeRejected(e.target.checked)}
                className="rounded border-gray-300"
              />
              Rejected ({counts.reject})
            </label>
            <label className="flex items-center gap-2 text-sm cursor-pointer">
              <input
                type="checkbox"
                checked={includeUnclear}
                onChange={(e) => setIncludeUnclear(e.target.checked)}
                className="rounded border-gray-300"
              />
              Unclear ({counts.unclear})
            </label>
          </div>
        </div>

        <div className="space-y-1 text-xs text-muted-foreground">
          <p>• Confirmed = model label kept as-is. Reclassified = your corrected class is used.</p>
          <p>
            • Rejected = image enters as background (empty label) for false-positive suppression.
          </p>
          <p>• Unclear = ambiguous; never becomes a label.</p>
        </div>
        {onlyNegatives && (
          <div className="rounded-md border border-yellow-500/30 bg-yellow-500/10 p-3 text-sm text-yellow-600 dark:text-yellow-400">
            Warning: only rejected reviews selected — the dataset will contain empty-label
            (background) images only. Mix it into a clean dataset for hard-negative training; never
            train on it alone.
          </div>
        )}
        {/* Form fields */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Stage</label>
            <select
              value={stage}
              onChange={(e) => setStage(e.target.value as DatasetStage)}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            >
              <option value="stage1">Stage 1 (SOD)</option>
              <option value="stage2">Stage 2 (7-class defect)</option>
              <option value="stage3">Stage 3 (21-class panel)</option>
            </select>
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Version Name</label>
            <input
              type="text"
              value={versionName}
              onChange={(e) => setVersionName(e.target.value)}
              placeholder="e.g. v2.1_flywheel"
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-sm font-medium">Notes (optional)</label>
            <input
              type="text"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Optional notes..."
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
          </div>
        </div>

        {/* Build button */}
        <div className="flex items-center gap-3">
          <Button
            onClick={handleBuild}
            disabled={!canBuild || building}
            title={
              !canBuild ? "Enter a version name and select at least one review type" : undefined
            }
          >
            {building ? (
              <>
                <Loader2 className="h-4 w-4 mr-1.5 animate-spin" />
                Building...
              </>
            ) : (
              <>
                <Hammer className="h-4 w-4 mr-1.5" />
                Build Dataset ({totalSelected} items)
              </>
            )}
          </Button>
          {totalSelected === 0 && (
            <span className="text-xs text-muted-foreground">No items selected</span>
          )}
        </div>

        {/* Result */}
        {error && (
          <div className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-600 dark:text-red-400">
            Error: {error}
          </div>
        )}
        {result && (
          <div className="rounded-md border border-green-500/30 bg-green-500/10 p-3 text-sm space-y-1">
            <p className="font-medium text-green-700 dark:text-green-400">
              Dataset build registered: {result.version_name}
            </p>
            <p className="text-muted-foreground">{result.message}</p>
          </div>
        )}
      </div>
    </div>
  );
}
