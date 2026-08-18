import { useEffect, useState } from "react";
import type {
  ExperimentSummary,
  ExperimentRun,
} from "@/lib/inspection/experimentSchema";
import {
  fetchExperiments,
  fetchExperimentRuns,
  compareRuns,
} from "@/lib/inspection/apiClient";
import { ExperimentList } from "./ExperimentList";
import { RunComparisonTable } from "./RunComparisonTable";
import { FlaskConical, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";

export function ExperimentDashboard() {
  const [experiments, setExperiments] = useState<ExperimentSummary[]>([]);
  const [selectedExpId, setSelectedExpId] = useState<string | null>(null);
  const [runs, setRuns] = useState<ExperimentRun[]>([]);
  const [bestRunId, setBestRunId] = useState<string | null>(null);
  const [loadingExperiments, setLoadingExperiments] = useState(true);
  const [loadingRuns, setLoadingRuns] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadExperiments = async () => {
    try {
      setLoadingExperiments(true);
      setError(null);
      const res = await fetchExperiments();
      setExperiments(res.experiments);
      // Auto-select first experiment
      if (res.experiments.length > 0 && !selectedExpId) {
        setSelectedExpId(res.experiments[0].experiment_id);
      }
    } catch (err: any) {
      setError(err.message || "Failed to load experiments");
    } finally {
      setLoadingExperiments(false);
    }
  };

  const loadRuns = async (expId: string) => {
    try {
      setLoadingRuns(true);
      const res = await fetchExperimentRuns(expId);
      setRuns(res.runs);

      // Find best run by mAP50(M)
      let bestId: string | null = null;
      let bestMap = -1;
      for (const run of res.runs) {
        const map50 = run.metrics.find((m) => m.key === "metrics/mAP50(M)");
        if (map50 && map50.value > bestMap) {
          bestMap = map50.value;
          bestId = run.run_id;
        }
      }
      setBestRunId(bestId);
    } catch (err: any) {
      setError(err.message || "Failed to load runs");
    } finally {
      setLoadingRuns(false);
    }
  };

  useEffect(() => {
    loadExperiments();
  }, []);

  useEffect(() => {
    if (selectedExpId) {
      loadRuns(selectedExpId);
    }
  }, [selectedExpId]);

  const selectedExp = experiments.find((e) => e.experiment_id === selectedExpId);

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight flex items-center gap-2">
            <FlaskConical className="h-6 w-6" />
            Experiments
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Compare MLflow training runs and identify the best models.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadExperiments}>
          <RefreshCw className="h-4 w-4 mr-1.5" />
          Refresh
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="grid grid-cols-12 gap-6">
        {/* Left: Experiment List */}
        <div className="col-span-3">
          <div className="rounded-lg border border-border bg-card">
            <div className="border-b border-border px-4 py-3">
              <h3 className="text-sm font-semibold">Experiments</h3>
            </div>
            <div className="p-2">
              <ExperimentList
                experiments={experiments}
                selectedId={selectedExpId}
                onSelect={setSelectedExpId}
                loading={loadingExperiments}
              />
            </div>
          </div>
        </div>

        {/* Right: Runs Table */}
        <div className="col-span-9 space-y-4">
          {selectedExp && (
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold">{selectedExp.name}</h2>
              <span className="text-xs text-muted-foreground">
                {runs.length} runs
              </span>
            </div>
          )}

          {loadingRuns ? (
            <div className="rounded-lg border border-border bg-card p-8 text-center text-muted-foreground">
              Loading runs...
            </div>
          ) : (
            <RunComparisonTable runs={runs} bestRunId={bestRunId} />
          )}
        </div>
      </div>
    </div>
  );
}
