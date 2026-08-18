import { useEffect, useState } from "react";
import { Loader2, CheckCircle2, XCircle } from "lucide-react";
import { getChainRunStatus } from "@/lib/inspection/apiClient";
import type { ChainRunStatusResponse } from "@/lib/inspection/platformSchema";

interface Props {
  runId: string;
}

export function ChainRunStatus({ runId }: Props) {
  const [status, setStatus] = useState<ChainRunStatusResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const poll = async () => {
      try {
        const res = await getChainRunStatus(runId);
        if (!cancelled) setStatus(res);
        if (res.status === "completed" || res.status === "failed") {
          cancelled = true;
          return;
        }
      } catch (e) {
        if (!cancelled) setError(e instanceof Error ? e.message : "Failed to fetch status");
      }
      if (!cancelled) setTimeout(poll, 3000);
    };
    poll();
    return () => {
      cancelled = true;
    };
  }, [runId]);

  if (error) return <p className="text-xs text-destructive">{error}</p>;
  if (!status) return <p className="text-xs text-muted-foreground">Loading run status...</p>;

  return (
    <div className="rounded-md border border-border bg-card p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold">Chain Run Status</h4>
        <span className="font-mono text-xs text-muted-foreground">{status.status}</span>
      </div>
      <div className="space-y-2">
        {status.jobs.map((job) => (
          <div key={job.job_id} className="flex items-center gap-3 text-xs">
            {job.status === "running" ? (
              <Loader2 className="h-4 w-4 animate-spin text-primary" />
            ) : job.status === "completed" ? (
              <CheckCircle2 className="h-4 w-4 text-status-pass" />
            ) : job.status === "failed" || job.status === "cancelled" ? (
              <XCircle className="h-4 w-4 text-status-fail" />
            ) : (
              <div className="h-4 w-4 rounded-full border border-muted-foreground/50" />
            )}
            <span className="font-mono">Step {job.step_index}</span>
            <span className="text-muted-foreground">Job: {job.job_id.slice(0, 8)}...</span>
            <span className="ml-auto font-medium">{job.status}</span>
          </div>
        ))}
      </div>
      {status.error && <p className="text-xs text-status-fail">Error: {status.error}</p>}
    </div>
  );
}
