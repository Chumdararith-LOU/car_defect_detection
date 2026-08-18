import type { SuppressedDetection } from "@/lib/inspection/schema";
import { DEFECT_CLASSES, PANEL_LABELS } from "@/lib/inspection/constants";
import { getCropStyle } from "./cropStyle";
import { ReviewFooter } from "./ReviewFooter";

interface Props {
  suppressed: SuppressedDetection;
  imageUrl: string;
  inspectionId: string | null;
}

export function SuppressedCard({ suppressed, imageUrl, inspectionId }: Props) {
  const label =
    DEFECT_CLASSES.find((c) => c.id === suppressed.predicted_class)?.label ??
    suppressed.predicted_class;
  return (
    <div className="overflow-hidden rounded-sm border border-border bg-card opacity-70">
      <div className="relative aspect-[4/3] w-full" style={getCropStyle(imageUrl, suppressed.bbox)}>
        <svg viewBox="0 0 100 100" preserveAspectRatio="none" className="absolute inset-0 h-full w-full">
          {suppressed.polygon && suppressed.polygon.length > 0 ? (
            <polygon
              points={suppressed.polygon.map(([x, y]) => `${x * 100},${y * 100}`).join(" ")}
              fill="none"
              stroke="var(--border)"
              strokeWidth={1}
              strokeDasharray="2 2"
              vectorEffect="non-scaling-stroke"
            />
          ) : (
            <rect
              x={suppressed.bbox[0] * 100}
              y={suppressed.bbox[1] * 100}
              width={(suppressed.bbox[2] - suppressed.bbox[0]) * 100}
              height={(suppressed.bbox[3] - suppressed.bbox[1]) * 100}
              fill="none"
              stroke="var(--border)"
              strokeWidth={1}
              strokeDasharray="2 2"
              vectorEffect="non-scaling-stroke"
            />
          )}
        </svg>
        <div className="absolute left-2 top-2 flex items-center gap-1.5 rounded-sm bg-background/90 px-2 py-0.5 font-mono text-[10px] font-medium uppercase backdrop-blur">
          <span className="h-1.5 w-1.5 rounded-full bg-muted-foreground" />
          <span className="line-through">{label}</span>
        </div>
        <div className="absolute right-2 top-2 rounded-sm bg-background/90 px-2 py-0.5 font-mono text-[10px] font-medium backdrop-blur">
          {(suppressed.confidence * 100).toFixed(0)}%
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 p-3 text-[11px]">
        <div>
          <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">Panel</p>
          <p className="font-medium">{PANEL_LABELS[suppressed.panel] ?? suppressed.panel}</p>
        </div>
        <div>
          <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">Reason</p>
          <p className="font-mono text-muted-foreground capitalize">
            {suppressed.reason.replace("_", " ")}
          </p>
        </div>
        <div className="col-span-2 border-t border-border pt-2">
          <ReviewFooter
            inspectionId={inspectionId}
            predictedClass={suppressed.predicted_class}
            predictedPanel={suppressed.panel}
            defectId={suppressed.id}
          />
        </div>
      </div>
    </div>
  );
}
