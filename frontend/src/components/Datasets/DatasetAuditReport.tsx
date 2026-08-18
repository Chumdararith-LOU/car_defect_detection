import { AlertTriangle, CheckCircle2, FlaskConical, XCircle } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { AuditReport } from "@/lib/inspection/platformSchema";

interface Props {
  report: AuditReport | null;
  loading: boolean;
  running: boolean;
  error: string | null;
  onRun: () => void;
}

export function DatasetAuditReport({ report, loading, running, error, onRun }: Props) {
  return (
    <div className="space-y-3 rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-2 text-sm font-semibold">
          <FlaskConical className="h-4 w-4 text-muted-foreground" />
          Training Readiness Audit
        </h3>
        <Button size="sm" variant="outline" onClick={onRun} disabled={running || loading}>
          {running ? "Auditing..." : report ? "Re-run Full Audit" : "Run Full Audit"}
        </Button>
      </div>
      {error && <p className="text-xs text-destructive">{error}</p>}
      {loading && <p className="text-xs text-muted-foreground">Loading audit report...</p>}
      {!loading && !report && !error && (
        <p className="text-xs text-muted-foreground">
          No audit report yet. Run the full audit to check size buckets, label validity, and
          training clearance.
        </p>
      )}
      {report && (
        <div className="space-y-4">
          {report.cleared_for_training ? (
            <div className="flex items-center gap-2 rounded-md border border-status-pass/30 bg-status-pass/10 p-3 text-xs text-status-pass">
              <CheckCircle2 className="h-4 w-4 shrink-0" />
              <span>
                Cleared for training · computed {new Date(report.computed_at).toLocaleString()}
              </span>
            </div>
          ) : (
            <div className="rounded-md border border-status-fail/30 bg-status-fail/10 p-3 text-xs text-status-fail">
              <p className="flex items-center gap-2">
                <XCircle className="h-4 w-4 shrink-0" />
                Blocked for training
              </p>
              <ul className="mt-1 list-disc space-y-0.5 pl-6">
                {report.blocking_reasons.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
            </div>
          )}
          {report.warnings.length > 0 && (
            <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-400">
              <p className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                Warnings
              </p>
              <ul className="mt-1 list-disc space-y-0.5 pl-6">
                {report.warnings.map((w) => (
                  <li key={w}>{w}</li>
                ))}
              </ul>
            </div>
          )}
          <div className="grid grid-cols-3 gap-2 md:grid-cols-6">
            <div className="rounded-md border border-border bg-muted/30 p-2 text-center">
              <p className="text-[10px] font-mono uppercase text-muted-foreground">Images</p>
              <p className="font-mono text-sm font-semibold">
                {report.totals.images.toLocaleString()}
              </p>
            </div>
            <div className="rounded-md border border-border bg-muted/30 p-2 text-center">
              <p className="text-[10px] font-mono uppercase text-muted-foreground">Instances</p>
              <p className="font-mono text-sm font-semibold">
                {report.totals.instances.toLocaleString()}
              </p>
            </div>
            <div className="rounded-md border border-border bg-muted/30 p-2 text-center">
              <p className="text-[10px] font-mono uppercase text-muted-foreground">Missing lbl</p>
              <p className="font-mono text-sm font-semibold">
                {report.label_issues.missing_label_images}
              </p>
            </div>
            <div className="rounded-md border border-border bg-muted/30 p-2 text-center">
              <p className="text-[10px] font-mono uppercase text-muted-foreground">Empty lbl</p>
              <p className="font-mono text-sm font-semibold">
                {report.label_issues.empty_label_images}
              </p>
            </div>
            <div className="rounded-md border border-border bg-muted/30 p-2 text-center">
              <p className="text-[10px] font-mono uppercase text-muted-foreground">Bad lines</p>
              <p className="font-mono text-sm font-semibold">
                {report.label_issues.unparseable_lines}
              </p>
            </div>
            <div className="rounded-md border border-border bg-muted/30 p-2 text-center">
              <p className="text-[10px] font-mono uppercase text-muted-foreground">Bad ids</p>
              <p className="font-mono text-sm font-semibold">
                {report.label_issues.out_of_range_class_ids}
              </p>
            </div>
          </div>
          <div className="space-y-1">
            <h4 className="text-xs font-semibold">Annotation size buckets (relative area)</h4>
            <div className="grid grid-cols-3 gap-2 text-center">
              <div className="rounded-md border border-border bg-muted/30 p-2">
                <p className="text-[10px] font-mono uppercase text-muted-foreground">Bottom 10%</p>
                <p className="font-mono text-sm font-semibold">
                  {report.size_buckets.bottom_10_count}
                </p>
              </div>
              <div className="rounded-md border border-border bg-muted/30 p-2">
                <p className="text-[10px] font-mono uppercase text-muted-foreground">Middle 50%</p>
                <p className="font-mono text-sm font-semibold">
                  {report.size_buckets.middle_50_count}
                </p>
              </div>
              <div className="rounded-md border border-border bg-muted/30 p-2">
                <p className="text-[10px] font-mono uppercase text-muted-foreground">Top 40%</p>
                <p className="font-mono text-sm font-semibold">
                  {report.size_buckets.top_40_count}
                </p>
              </div>
            </div>
            <p className="font-mono text-[10px] text-muted-foreground">
              p10={report.size_buckets.p10_area} · p60={report.size_buckets.p60_area}
            </p>
          </div>
          {report.rare_classes.length > 0 && (
            <div className="space-y-1">
              <h4 className="text-xs font-semibold">Rare classes</h4>
              <div className="flex flex-wrap gap-1.5">
                {report.rare_classes.map((c) => (
                  <span
                    key={c}
                    className="rounded-sm border border-amber-500/30 bg-amber-500/10 px-1.5 py-0.5 font-mono text-[10px] text-amber-700 dark:text-amber-400"
                  >
                    {c}
                  </span>
                ))}
              </div>
            </div>
          )}
          {report.stage === "stage1" && (
            <p className="text-[10px] text-muted-foreground">
              Semantic-mask dataset — YOLO label checks skipped.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
