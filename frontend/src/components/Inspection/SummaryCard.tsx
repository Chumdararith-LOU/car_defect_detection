import type { InspectionPayload } from "@/lib/inspection/schema";
import { cn } from "@/lib/utils";
import { Car, AlertOctagon, CheckCircle2 } from "lucide-react";

export function SummaryCard({
  payload,
  filteredCount,
  disabledStages,
}: {
  payload: InspectionPayload | null;
  filteredCount: number;
  disabledStages?: string[];
}) {
  if (!payload) {
    return (
      <div className="rounded-sm border border-border bg-card p-4">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
          Master inspection summary
        </p>
        <p className="mt-2 text-xs text-muted-foreground">Run an inspection to see the report.</p>
      </div>
    );
  }

  const fail = payload.inspection_status === "FAIL";
  const stage1Disabled = payload.preScreen == null || (disabledStages?.includes("stage1") ?? false);
  const stage3Disabled =
    (payload.panels?.length ?? 0) === 0 || (disabledStages?.includes("stage3") ?? false);

  return (
    <div className="rounded-sm border border-border bg-card p-4">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
            Master inspection summary
          </p>
          <h3 className="mt-1 flex items-center gap-2 text-base font-semibold">
            <Car className="h-4 w-4 text-muted-foreground" />
            {payload.vehicle_color_detected}
          </h3>
        </div>
        <div
          className={cn(
            "flex items-center gap-1.5 rounded-sm px-3 py-1.5 font-mono text-sm font-bold uppercase tracking-wide",
            fail ? "bg-status-fail/15 text-status-fail" : "bg-status-pass/15 text-status-pass",
          )}
        >
          {fail ? <AlertOctagon className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
          {payload.inspection_status}
        </div>
      </div>

      <dl className="mt-3 grid grid-cols-3 gap-3 text-[11px]">
        <div>
          <dt className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
            Pre-screen
          </dt>
          {stage1Disabled ? (
            <>
              <dd className="font-mono text-sm">—</dd>
              <dd className="text-[9px] text-muted-foreground/70">Stage 1 disabled</dd>
            </>
          ) : (
            <dd className="font-mono text-sm">
              {payload.preScreen?.anomalyDetected ? "Anomaly" : "Clean"}
              {payload.preScreen?.score != null && (
                <span className="text-muted-foreground">
                  {" "}
                  ({payload.preScreen.score.toFixed(2)})
                </span>
              )}
            </dd>
          )}
        </div>
        <div>
          <dt className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
            Panels
          </dt>
          {stage3Disabled ? (
            <>
              <dd className="font-mono text-sm">—</dd>
              <dd className="text-[9px] text-muted-foreground/70">Stage 3 disabled</dd>
            </>
          ) : (
            <dd className="font-mono text-sm">{payload.panels?.length}</dd>
          )}
        </div>
        <div>
          <dt className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
            Defects
          </dt>
          <dd className="font-mono text-sm">
            {filteredCount}
            <span className="text-muted-foreground"> / {payload.defects.length} shown</span>
          </dd>
        </div>
        <div>
          <dt className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
            Image
          </dt>
          <dd className="font-mono text-sm">
            {payload.imageDims ? `${payload.imageDims.width}×${payload.imageDims.height}` : "—"}
          </dd>
        </div>
        <div>
          <dt className="font-mono text-[9px] uppercase tracking-wider text-muted-foreground">
            Time
          </dt>
          <dd className="font-mono text-[10px] leading-4">
            {new Date(payload.timestamp).toLocaleTimeString()}
          </dd>
        </div>
      </dl>
    </div>
  );
}
