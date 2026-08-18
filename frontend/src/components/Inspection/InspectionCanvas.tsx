import { useMemo } from "react";
import type {
  Defect,
  InspectionPayload,
  ViewStage,
} from "@/lib/inspection/schema";
import {
  classColor,
  PANEL_LABELS,
  panelColor,
} from "@/lib/inspection/constants";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";

function toPoints(polygon: [number, number][], w: number, h: number) {
  return polygon.map(([x, y]) => `${x * w},${y * h}`).join(" ");
}

function defectMatchesViewStage(d: Defect, viewStage: ViewStage): boolean {
  const isAnomaly = d.class === "anomaly";
  if (viewStage === 1) return isAnomaly;
  // Stage 2 and Stage 3 both show real (non-anomaly) defects
  return !isAnomaly;
}

interface Props {
  imageUrl: string;
  payload: InspectionPayload | null;
  visibleDefects: Defect[];
  hoveredId: string | null;
  onHover: (id: string | null) => void;
  viewStage?: ViewStage;
}

export function InspectionCanvas({
  imageUrl,
  payload,
  visibleDefects,
  hoveredId,
  onHover,
  viewStage = 2,
}: Props) {
  const { W, H } = useMemo(() => {
    const dims = payload?.imageDims;
    return { W: dims?.width ?? 1600, H: dims?.height ?? 900 };
  }, [payload]);

  const preScreenChip = payload
    ? payload.preScreen?.anomalyDetected
      ? { label: "Active Route", tone: "warn" as const }
      : { label: "Pass", tone: "pass" as const }
    : { label: "Awaiting run", tone: "idle" as const };

  const visibleIds = new Set(visibleDefects.map((d) => d.id));

  return (
    <div className="relative flex h-full flex-col">
      <div className="flex items-center justify-between border-b border-border px-5 py-3">
        <div>
          <p className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground ">
            Zone B · Global Spatial Context
          </p>
          <h2 className="mt-0.5 text-sm font-semibold uppercase tracking-wide ">
            High-resolution canvas
          </h2>
        </div>
        <div
          className={cn(
            "flex items-center gap-2 rounded-sm border px-3 py-1 font-mono text-[11px] font-medium uppercase tracking-wide ",
            preScreenChip.tone === "pass" &&
              "border-status-pass/40 bg-status-pass/10 text-status-pass",
            preScreenChip.tone === "warn" &&
              "border-amber-500/40 bg-amber-500/10 text-amber-600 dark:text-amber-400",
            preScreenChip.tone === "idle" &&
              "border-border text-muted-foreground",
          )}
        >
          <span
            className={cn(
              "h-1.5 w-1.5 rounded-full",
              preScreenChip.tone === "pass" && "bg-status-pass",
              preScreenChip.tone === "warn" && "bg-amber-500 animate-pulse",
              preScreenChip.tone === "idle" && "bg-muted-foreground",
            )}
          />
          Pre-screen: {preScreenChip.label}
          {payload && payload.inspection_status === "FAIL" && (
            <span className="text-muted-foreground">
              · {payload.total_defects_found} defect(s)
            </span>
          )}
        </div>
      </div>

      <div className="relative flex-1 overflow-hidden bg-black/10 p-4 dark:bg-black/60">
        <div className="relative mx-auto h-full w-full max-w-[1400px] rounded-sm border border-border/40">
          <div className="relative h-full w-full">
            <img
              src={imageUrl}
              alt="Vehicle under inspection"
              className="absolute inset-0 h-full w-full object-contain"
            />
            {payload && (
              <svg
                viewBox={`0 0 ${W} ${H}`}
                className="absolute inset-0 h-full w-full"
                preserveAspectRatio="xMidYMid meet"
              >
                {/* Stage 1 saliency blobs (S1 pre-screen view) */}
                {viewStage === 1 &&
                  Array.isArray(payload.stage1_blobs) &&
                  payload.stage1_blobs.map((b) => (
                    <g key={b.id}>
                      {b.polygon && b.polygon.length > 0 ? (
                        <polygon
                          points={toPoints(b.polygon, W, H)}
                          fill="var(--defect-anomaly)"
                          fillOpacity={0.35}
                          stroke="var(--defect-anomaly)"
                          strokeWidth={1.5}
                        />
                      ) : (
                        <rect
                          x={b.bbox[0] * W}
                          y={b.bbox[1] * H}
                          width={(b.bbox[2] - b.bbox[0]) * W}
                          height={(b.bbox[3] - b.bbox[1]) * H}
                          fill="var(--defect-anomaly)"
                          fillOpacity={0.35}
                          stroke="var(--defect-anomaly)"
                          strokeWidth={1.5}
                        />
                      )}
                    </g>
                  ))}
                {/* Panel outlines (Safe check: ensure panels is an array) */}
                {Array.isArray(payload.panels) &&
                  payload.panels.map((p) => (
                    <polygon
                      key={p.id}
                      points={p.polygon
                        .map(([x, y]) => `${x * W},${y * H}`)
                        .join(" ")}
                      fill={viewStage === 3 ? panelColor(p.label) : "none"}
                      fillOpacity={viewStage === 3 ? 0.35 : 0}
                      stroke={
                        viewStage === 3 ? panelColor(p.label) : "currentColor"
                      }
                      strokeWidth={viewStage === 3 ? 2 : 1.5}
                      strokeDasharray="6 4"
                      className={viewStage === 3 ? "" : "text-primary/40"}
                    />
                  ))}
                {/* Panel labels (Safe check) */}
                {Array.isArray(payload.panels) &&
                  payload.panels?.map((p) => {
                    if (!p.polygon || p.polygon.length === 0) return null;
                    const cx =
                      (p.polygon.reduce((s, pt) => s + pt[0], 0) /
                        p.polygon.length) *
                      W;
                    const cy =
                      (p.polygon.reduce((s, pt) => s + pt[1], 0) /
                        p.polygon.length) *
                      H;
                    return (
                      <text
                        key={`t-${p.id}`}
                        x={cx}
                        y={cy}
                        fontSize={11}
                        textAnchor="middle"
                        className={
                          viewStage === 3
                            ? "font-mono uppercase"
                            : "fill-primary/60 font-mono uppercase"
                        }
                        style={{
                          pointerEvents: "none",
                          ...(viewStage === 3
                            ? { fill: panelColor(p.label) }
                            : {}),
                        }}
                      >
                        {p.label}
                      </text>
                    );
                  })}

                {/* Panel labels (Safe check) */}
                {Array.isArray(payload.panels) &&
                  payload.panels?.map((p) => {
                    if (!p.polygon || p.polygon.length === 0) return null;
                    const cx =
                      (p.polygon.reduce((s, pt) => s + pt[0], 0) /
                        p.polygon.length) *
                      W;
                    const cy =
                      (p.polygon.reduce((s, pt) => s + pt[1], 0) /
                        p.polygon.length) *
                      H;
                    return (
                      <text
                        key={`t-${p.id}`}
                        x={cx}
                        y={cy}
                        fontSize={11}
                        textAnchor="middle"
                        className={
                          viewStage === 3
                            ? "font-mono uppercase"
                            : "fill-primary/60 font-mono uppercase"
                        }
                        style={{
                          pointerEvents: "none",
                          ...(viewStage === 3
                            ? { fill: panelColor(p.label) }
                            : {}),
                        }}
                      >
                        {p.label}
                      </text>
                    );
                  })}

                {/* Defect polygons (Safe check for bbox and polygon) */}
                {payload.defects.map((d) => {
                  if (!defectMatchesViewStage(d, viewStage)) return null;
                  const visible = visibleIds.has(d.id);
                  const isHover = hoveredId === d.id;
                  const color = classColor(d.class);

                  // Safe fallbacks in case backend sends undefined
                  const bbox = d.bbox ?? [0, 0, 0, 0];
                  const poly = d.polygon ?? [];

                  return (
                    <g
                      key={d.id}
                      onMouseEnter={() => onHover(d.id)}
                      onMouseLeave={() => onHover(null)}
                      style={{ cursor: "pointer", opacity: visible ? 1 : 0.1 }}
                    >
                      {poly.length > 0 && (
                        <polygon
                          points={toPoints(poly, W, H)}
                          fill={color}
                          fillOpacity={isHover ? 0.55 : 0.3}
                          stroke={color}
                          strokeWidth={isHover ? 3 : 1.5}
                        />
                      )}
                      {/* Emphasis ring for tiny defects (Fixed math precedence) */}
                      <circle
                        cx={((bbox[0] + bbox[2]) / 2) * W}
                        cy={((bbox[1] + bbox[3]) / 2) * H}
                        r={isHover ? 28 : 20}
                        fill="none"
                        stroke={color}
                        strokeWidth={isHover ? 2 : 1}
                        strokeOpacity={0.7}
                      />
                    </g>
                  );
                })}
              </svg>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
