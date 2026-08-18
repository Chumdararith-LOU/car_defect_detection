import type { UnclassifiedAnomaly } from "@/lib/inspection/schema";
import { PANEL_LABELS } from "@/lib/inspection/constants";
import { getCropStyle } from "./cropStyle";
import { ReviewFooter } from "./ReviewFooter";

interface Props {
  anomaly: UnclassifiedAnomaly;
  imageUrl: string;
  inspectionId: string | null;
}

export function AnomalyCard({ anomaly, imageUrl, inspectionId }: Props) {
  return (
    <div className="overflow-hidden rounded-sm border border-amber-500/50 bg-card">
      <div className="relative aspect-[4/3] w-full" style={getCropStyle(imageUrl, anomaly.bbox)}>
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          className="absolute inset-0 h-full w-full"
        >
          {anomaly.polygon && anomaly.polygon.length > 0 ? (
            <polygon
              points={anomaly.polygon.map(([x, y]) => `${x * 100},${y * 100}`).join(" ")}
              fill="none"
              stroke="var(--defect-anomaly)"
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
          ) : (
            <rect
              x={anomaly.bbox[0] * 100}
              y={anomaly.bbox[1] * 100}
              width={(anomaly.bbox[2] - anomaly.bbox[0]) * 100}
              height={(anomaly.bbox[3] - anomaly.bbox[1]) * 100}
              fill="none"
              stroke="var(--defect-anomaly)"
              strokeWidth={1}
              vectorEffect="non-scaling-stroke"
            />
          )}
        </svg>
        <div className="absolute left-2 top-2 flex items-center gap-1.5 rounded-sm bg-background/90 px-2 py-0.5 font-mono text-[10px] font-medium uppercase backdrop-blur">
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: "var(--defect-anomaly)" }}
          />
          Anomaly (Rescued)
        </div>
        <div className="absolute right-2 top-2 rounded-sm bg-background/90 px-2 py-0.5 font-mono text-[10px] font-medium backdrop-blur">
          {(anomaly.confidence * 100).toFixed(0)}%
        </div>
      </div>
      <div className="grid grid-cols-2 gap-2 p-3 text-[11px]">
        <div className="col-span-2">
          <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
            Panel
          </p>
          {!anomaly.panel || anomaly.panel === "Unknown" ? (
            <span className="inline-block rounded-sm border border-border bg-muted/40 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              Unknown panel
            </span>
          ) : (
            <p className="font-medium">{PANEL_LABELS[anomaly.panel] ?? anomaly.panel}</p>
          )}
        </div>
        {anomaly.low_context && (
          <div className="col-span-2">
            <span className="inline-block rounded-sm border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-amber-600 dark:text-amber-400">
              low context
            </span>
          </div>
        )}
        <div className="col-span-2">
          <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
            Reason
          </p>
          <p className="font-mono text-amber-500">{anomaly.reason}</p>
        </div>
        <div className="col-span-2 border-t border-border pt-2">
          <ReviewFooter
            inspectionId={inspectionId}
            predictedClass="anomaly"
            predictedPanel={anomaly.panel}
            defectId={anomaly.id}
          />
        </div>
      </div>
    </div>
  );
}
