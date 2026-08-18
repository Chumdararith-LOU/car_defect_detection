import type { ExperimentRun } from "@/lib/inspection/experimentSchema";
import { Trophy, Clock } from "lucide-react";

interface Props {
  runs: ExperimentRun[];
  bestRunId: string | null;
}

const METRIC_KEYS = [
  "metrics/mAP50(M)",
  "metrics/mAP50-95(M)",
  "metrics/precision(M)",
  "metrics/recall(M)",
];

const METRIC_LABELS: Record<string, string> = {
  "metrics/mAP50(M)": "mAP50 (Mask)",
  "metrics/mAP50-95(M)": "mAP50-95 (Mask)",
  "metrics/precision(M)": "Precision",
  "metrics/recall(M)": "Recall",
};

const PARAM_KEYS = ["model_preset", "epochs", "imgsz", "batch_size", "loss_type"];

function formatDuration(seconds: number | null): string {
  if (seconds === null) return "—";
  if (seconds < 60) return `${Math.round(seconds)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}

function getMetricValue(run: ExperimentRun, key: string): number | null {
  const metric = run.metrics.find((m) => m.key === key);
  return metric ? metric.value : null;
}

function getParamValue(run: ExperimentRun, key: string): string | null {
  const param = run.params.find((p) => p.key === key);
  return param ? param.value : null;
}

function findBestMetricValue(runs: ExperimentRun[], key: string): number | null {
  const values = runs
    .map((r) => getMetricValue(r, key))
    .filter((v): v is number => v !== null);
  if (values.length === 0) return null;
  return Math.max(...values);
}

export function RunComparisonTable({ runs, bestRunId }: Props) {
  if (runs.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-border p-8 text-center text-muted-foreground">
        Select an experiment to view its runs.
      </div>
    );
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-xs uppercase tracking-wider text-muted-foreground">
          <tr>
            <th className="px-4 py-3 text-left font-medium">Run</th>
            <th className="px-4 py-3 text-left font-medium">Status</th>
            <th className="px-4 py-3 text-left font-medium">Duration</th>
            {METRIC_KEYS.map((key) => (
              <th key={key} className="px-4 py-3 text-right font-medium">
                {METRIC_LABELS[key]}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-border bg-card">
          {runs.map((run) => {
            const isBest = run.run_id === bestRunId;
            return (
              <tr
                key={run.run_id}
                className={`transition-colors ${
                  isBest ? "bg-green-500/5" : "hover:bg-muted/30"
                }`}
              >
                <td className="px-4 py-3">
                  <div className="flex items-center gap-2">
                    {isBest && <Trophy className="h-3.5 w-3.5 text-yellow-500" />}
                    <div>
                      <p className="font-medium text-sm">{run.run_name}</p>
                      <p className="text-[10px] font-mono text-muted-foreground">
                        {run.run_id.substring(0, 8)}...
                      </p>
                    </div>
                  </div>
                </td>
                <td className="px-4 py-3">
                  <span
                    className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${
                      run.status === "FINISHED"
                        ? "bg-green-500/15 text-green-700 dark:text-green-400"
                        : run.status === "RUNNING"
                        ? "bg-blue-500/15 text-blue-700 dark:text-blue-400"
                        : "bg-gray-500/15 text-gray-700 dark:text-gray-400"
                    }`}
                  >
                    {run.status}
                  </span>
                </td>
                <td className="px-4 py-3 text-xs text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {formatDuration(run.duration_seconds)}
                  </div>
                </td>
                {METRIC_KEYS.map((key) => {
                  const value = getMetricValue(run, key);
                  const bestValue = findBestMetricValue(runs, key);
                  const isBestMetric = value !== null && value === bestValue;
                  return (
                    <td
                      key={key}
                      className={`px-4 py-3 text-right font-mono text-xs ${
                        isBestMetric
                          ? "font-semibold text-green-600 dark:text-green-400"
                          : "text-muted-foreground"
                      }`}
                    >
                      {value !== null ? (value * 100).toFixed(1) + "%" : "—"}
                    </td>
                  );
                })}
              </tr>
            );
          })}
        </tbody>
      </table>

      {/* Parameters footer */}
      <div className="border-t border-border bg-muted/30 p-4">
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="text-muted-foreground">
                <th className="px-4 py-2 text-left font-medium">Parameter</th>
                {runs.map((run) => (
                  <th key={run.run_id} className="px-4 py-2 text-left font-medium">
                    {run.run_name}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="font-mono">
              {PARAM_KEYS.map((key) => (
                <tr key={key} className="border-t border-border/50">
                  <td className="px-4 py-2 text-muted-foreground">{key}</td>
                  {runs.map((run) => (
                    <td key={run.run_id} className="px-4 py-2">
                      {getParamValue(run, key) || "—"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
