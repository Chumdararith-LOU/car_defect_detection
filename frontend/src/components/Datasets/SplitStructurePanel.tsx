import type { SplitLayout, SplitStructure } from "@/lib/inspection/prepSchema";
import { AlertTriangle, CheckCircle2, FileQuestion } from "lucide-react";

interface Props {
  structure: SplitStructure;
}

const LAYOUT_BADGE: Record<SplitLayout, { label: string; className: string }> = {
  ultralytics: {
    label: "Ultralytics",
    className:
      "bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/30",
  },
  grouped: {
    label: "Grouped",
    className:
      "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30",
  },
  unsplit: {
    label: "Unsplit",
    className:
      "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30",
  },
  flat: {
    label: "Flat",
    className:
      "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30",
  },
  unknown: {
    label: "Unknown",
    className: "bg-red-500/15 text-red-700 dark:text-red-400 border-red-500/30",
  },
};

const GRID_COLS: Record<number, string> = {
  1: "grid-cols-1",
  2: "grid-cols-2",
  3: "grid-cols-3",
};

export function SplitStructurePanel({ structure }: Props) {
  const layout = LAYOUT_BADGE[structure.layout];
  const gridClass = GRID_COLS[structure.splits.length] ?? "grid-cols-3";
  const isSemantic = structure.splits.some(
    (s) => s.label_format === "semantic_mask"
  );

  return (
    <div className="space-y-4">
      {/* Header: layout badge + totals */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span
          className={`inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${layout.className}`}
        >
          {layout.label} layout
        </span>
        <div className="flex items-center gap-3 text-xs text-muted-foreground">
          <span>{structure.total_images.toLocaleString()} images</span>
        <span>
            {structure.total_labels.toLocaleString()}{" "}
            {isSemantic ? "masks" : "labels"}
          </span>
          {structure.has_data_yaml ? (
            <span className="inline-flex items-center gap-1 text-green-600 dark:text-green-400">
              <CheckCircle2 className="h-3 w-3" /> data.yaml
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-amber-600 dark:text-amber-400">
              <FileQuestion className="h-3 w-3" /> no data.yaml
            </span>
          )}
        </div>
      </div>

      {/* Split status summary */}
      <p className="text-xs text-muted-foreground">
        {structure.is_split
          ? structure.has_test
            ? "Already split into train / val / test."
            : "Already split into train / val."
          : "Not split yet — choose a ratio below to split before training."}
      </p>

      {/* Per-split cards */}
      {structure.splits.length > 0 && (
        <div className={`grid gap-2 ${gridClass}`}>
          {structure.splits.map((split) => (
            <div
              key={split.name}
              className="rounded-md border border-border bg-muted/30 p-3 text-center"
            >
              <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
                {split.name}
              </p>
              <p className="text-lg font-semibold">
                {split.image_count.toLocaleString()}
              </p>
              <p className="text-[10px] text-muted-foreground">
                {split.label_count.toLocaleString()}{" "}
                {split.label_format === "semantic_mask" ? "masks" : "labels"}
              </p>
            </div>
          ))}
        </div>
      )}

      {/* Warnings */}
      {structure.warnings.length > 0 && (
        <div className="space-y-1.5">
          {structure.warnings.map((warning, idx) => (
            <div
              key={idx}
              className="flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-400"
            >
              <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" />
              <span>{warning}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
