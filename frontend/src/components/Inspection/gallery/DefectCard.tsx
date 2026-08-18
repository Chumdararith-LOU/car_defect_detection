import type { Defect } from "@/lib/inspection/schema";
import { classColor, DEFECT_CLASSES, PANEL_LABELS } from "@/lib/inspection/constants";
import { cn } from "@/lib/utils";
import { cropBox, getCropStyle } from "./cropStyle";
import { ReviewFooter } from "./ReviewFooter";

interface Props {
  defect: Defect;
  imageUrl: string;
  isHovered: boolean;
  onHover: (id: string | null) => void;
  inspectionId: string | null;
}

export function DefectCard({ defect, imageUrl, isHovered, onHover, inspectionId }: Props) {
  const { x, y, w, h, cx, cy, cw, ch } = cropBox(defect.bbox);
  const label = DEFECT_CLASSES.find((c) => c.id === defect.class)?.label ?? defect.class;

  return (
    <div
      onMouseEnter={() => onHover(defect.id)}
      onMouseLeave={() => onHover(null)}
      className={cn(
        "group overflow-hidden rounded-sm border border-border bg-card transition",
        isHovered && "border-primary ring-1 ring-primary",
      )}
      data-defect-id={defect.id}
    >
      <div className="relative aspect-[4/3] w-full" style={getCropStyle(imageUrl, defect.bbox)}>
        <svg
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          className="absolute inset-0 h-full w-full"
        >
          <rect
            x={((x - cx) / cw) * 100}
            y={((y - cy) / ch) * 100}
            width={(w / cw) * 100}
            height={(h / ch) * 100}
            fill="none"
            stroke={classColor(defect.class)}
            strokeWidth={1}
            vectorEffect="non-scaling-stroke"
          />
        </svg>
        <div className="absolute left-2 top-2 flex items-center gap-1.5 rounded-sm bg-background/90 px-2 py-0.5 font-mono text-[10px] font-medium uppercase backdrop-blur">
          <span
            className="h-1.5 w-1.5 rounded-full"
            style={{ backgroundColor: classColor(defect.class) }}
          />
          {label}
        </div>
        <div className="absolute right-2 top-2 rounded-sm bg-background/90 px-2 py-0.5 font-mono text-[10px] font-medium backdrop-blur">
          {(defect.confidence * 100).toFixed(0)}%
        </div>
      </div>
      <div className="grid grid-cols-3 gap-2 p-3 text-[11px]">
        <div className="col-span-3">
          <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
            Panel
          </p>
          {!defect.panel || defect.panel === "Unknown" ? (
            <span className="inline-block rounded-sm border border-border bg-muted/40 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground">
              Unknown panel
            </span>
          ) : (
            <p className="font-medium">{PANEL_LABELS[defect.panel] ?? defect.panel}</p>
          )}
        </div>
        <div>
          <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">IoD</p>
          <p className="font-mono">{defect.iod.toFixed(3)}</p>
        </div>
        {defect.dsi != null && (
          <div>
            <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
              DSI
            </p>
            <p className="font-mono">{(defect.dsi * 100).toFixed(2)}%</p>
          </div>
        )}
        <div>
          <p className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
            Conf.
          </p>
          <p className="font-mono">{(defect.confidence * 100).toFixed(1)}%</p>
        </div>
        <details className="col-span-3 mt-1 text-[10px] text-muted-foreground">
          <summary className="cursor-pointer">bbox</summary>
          <p className="font-mono">[{defect.bbox.map((n) => n.toFixed(3)).join(", ")}]</p>
        </details>
        <div className="col-span-3 border-t border-border pt-2">
          <ReviewFooter
            inspectionId={inspectionId}
            predictedClass={defect.class}
            predictedPanel={defect.panel}
            defectId={defect.id}
          />
        </div>
      </div>
    </div>
  );
}
