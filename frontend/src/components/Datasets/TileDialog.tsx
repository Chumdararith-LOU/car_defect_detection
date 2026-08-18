import { useState } from "react";
import { Button } from "@/components/ui/button";
import { LayoutGrid, Loader2, X } from "lucide-react";
import type { TileResponse } from "@/lib/inspection/prepSchema";
import { tileDataset } from "@/lib/inspection/apiClient";

interface Props {
  datasetId: string;
  sourceDatasetName: string;
  onClose: () => void;
  onComplete: () => void;
}

interface TileSizePreset {
  label: string;
  value: number;
}

const TILE_SIZE_PRESETS: TileSizePreset[] = [
  { label: "640", value: 640 },
  { label: "1024", value: 1024 },
  { label: "Adaptive 2×2", value: 0 },
];

export function TileDialog({
  datasetId,
  sourceDatasetName,
  onClose,
  onComplete,
}: Props) {
  const [newDatasetId, setNewDatasetId] = useState(
    `${sourceDatasetName}_tiled`
  );
  const [tileSize, setTileSize] = useState(1024);
  const [overlap, setOverlap] = useState(0.15);
  const [minAreaRatio, setMinAreaRatio] = useState(0.01);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<TileResponse | null>(null);

  const handleTile = async () => {
    if (!newDatasetId.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      const res = await tileDataset(datasetId, {
        new_dataset_id: newDatasetId.trim(),
        tile_size: tileSize,
        overlap,
        min_area_ratio: minAreaRatio,
      });
      setResult(res);
      onComplete();
    } catch (err: any) {
      setError(err.message || "Failed to tile dataset");
    } finally {
      setSubmitting(false);
    }
  };

  // ---- Phase 2: result ----
  if (result) {
    return (
      <div
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        onClick={onClose}
      >
        <div
          className="w-full max-w-md space-y-4 rounded-lg border border-border bg-card p-6 shadow-xl"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Tiling Complete</h3>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
          <p className="text-sm text-muted-foreground">{result.message}</p>
          <div className="rounded-md border border-border bg-muted/30 p-4 text-center">
            <p className="text-3xl font-semibold">
              {result.tiles_generated.toLocaleString()}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              tiles generated
            </p>
            <p className="mt-2 text-xs text-muted-foreground">
              New dataset:{" "}
              <span className="font-mono">{result.new_dataset_id}</span>
            </p>
          </div>
          <div className="flex justify-end">
            <Button onClick={onClose}>Done</Button>
          </div>
        </div>
      </div>
    );
  }

  // ---- Phase 1: form ----
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={onClose}
    >
      <div
        className="w-full max-w-md space-y-4 rounded-lg border border-border bg-card p-6 shadow-xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">Tile Dataset</h3>
          <button
            onClick={onClose}
            className="text-muted-foreground hover:text-foreground"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <p className="text-xs text-muted-foreground">
          Creates a new dataset of image tiles. Use this before training Stage 1
          (SOD) or to improve small-defect recall.
        </p>

        {/* New dataset name */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">New Dataset Name</label>
          <input
            type="text"
            value={newDatasetId}
            onChange={(e) => setNewDatasetId(e.target.value)}
            placeholder="e.g. my_dataset_tiled"
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
        </div>

        {/* Tile size presets + input */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Tile Size</label>
          <div className="flex flex-wrap gap-2">
            {TILE_SIZE_PRESETS.map((preset) => (
              <button
                key={preset.label}
                onClick={() => setTileSize(preset.value)}
                className={`rounded-md border px-2.5 py-1.5 text-xs transition-colors ${
                  tileSize === preset.value
                    ? "border-foreground bg-muted"
                    : "border-border bg-muted/30 hover:bg-muted"
                }`}
              >
                {preset.label}
              </button>
            ))}
          </div>
          <input
            type="number"
            min={0}
            step={64}
            value={tileSize}
            onChange={(e) => setTileSize(Number(e.target.value))}
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          />
          <p className="text-[11px] text-muted-foreground">
            {tileSize === 0
              ? "Adaptive mode: splits each image into 4 overlapping halves (legacy Stage 1 SOD)."
              : `Fixed ${tileSize}×${tileSize} pixel tiles.`}
          </p>
        </div>

        {/* Overlap + min area ratio */}
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Overlap
            </label>
            <input
              type="number"
              min={0}
              max={0.9}
              step={0.05}
              value={overlap}
              onChange={(e) => setOverlap(Number(e.target.value))}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
            <p className="text-[11px] text-muted-foreground">
              {(overlap * 100).toFixed(0)}% overlap
            </p>
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">
              Min Area Ratio
            </label>
            <input
              type="number"
              min={0}
              max={1}
              step={0.01}
              value={minAreaRatio}
              onChange={(e) => setMinAreaRatio(Number(e.target.value))}
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
            />
            <p className="text-[11px] text-muted-foreground">
              Discard clipped fragments below this fraction
            </p>
          </div>
        </div>

        {error && <p className="text-xs text-destructive">{error}</p>}

        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose}>
            Cancel
          </Button>
          <Button
            onClick={handleTile}
            disabled={!newDatasetId.trim() || submitting}
          >
            {submitting ? (
              <>
                <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> Tiling...
              </>
            ) : (
              <>
                <LayoutGrid className="mr-1.5 h-4 w-4" /> Tile Dataset
              </>
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
