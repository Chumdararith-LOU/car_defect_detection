import { useState } from "react";
import { Button } from "@/components/ui/button";
import { ShieldCheck, ShieldAlert, Loader2 } from "lucide-react";
import type { LeakageAuditResult } from "@/lib/inspection/schema";
import { runLeakageAudit } from "@/lib/inspection/apiClient";

interface Props {
  datasetId: string;
}

export function LeakageAuditPanel({ datasetId }: Props) {
  const [result, setResult] = useState<LeakageAuditResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleAudit = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await runLeakageAudit(datasetId);
      setResult(res);
    } catch (err: any) {
      setError(err.message || "Audit failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-lg border border-border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold">Leakage Audit</h4>
        <Button variant="outline" size="sm" onClick={handleAudit} disabled={loading}>
          {loading ? (
            <>
              <Loader2 className="h-3.5 w-3.5 mr-1.5 animate-spin" />
              Auditing...
            </>
          ) : (
            "Run Filename Audit"
          )}
        </Button>
      </div>

      {error && <p className="text-xs text-destructive">Error: {error}</p>}

      {result && (
        <div className="space-y-2 text-xs">
          <div
            className={`flex items-center gap-2 font-medium ${
              result.passed
                ? "text-green-600 dark:text-green-400"
                : "text-red-600 dark:text-red-400"
            }`}
          >
            {result.passed ? (
              <ShieldCheck className="h-4 w-4" />
            ) : (
              <ShieldAlert className="h-4 w-4" />
            )}
            {result.passed
              ? "Passed: No filename leakage detected"
              : "Failed: Filename overlaps found"}
          </div>
          <p className="text-muted-foreground">
            Checked {result.total_checked} images across train/val/test splits.
          </p>
          {!result.passed && result.filename_overlaps.length > 0 && (
            <div className="mt-2 max-h-32 overflow-y-auto rounded border border-border bg-background p-2">
              <p className="font-medium mb-1">
                Overlapping files ({result.filename_overlaps.length}):
              </p>
              <ul className="list-disc list-inside font-mono text-[10px] space-y-0.5">
                {result.filename_overlaps.slice(0, 10).map((o) => (
                  <li key={o.filename}>
                    {o.filename}{" "}
                    <span className="text-muted-foreground">
                      ({o.found_in.join(", ")})
                    </span>
                  </li>
                ))}
                {result.filename_overlaps.length > 10 && (
                  <li className="text-muted-foreground">
                    ...and {result.filename_overlaps.length - 10} more
                  </li>
                )}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
