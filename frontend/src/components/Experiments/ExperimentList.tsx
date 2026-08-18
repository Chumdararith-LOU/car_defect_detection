import type { ExperimentSummary } from "@/lib/inspection/experimentSchema";
import { FlaskConical } from "lucide-react";

interface Props {
  experiments: ExperimentSummary[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  loading: boolean;
}

function formatTimestamp(ts: string | null): string {
  if (!ts) return "—";
  const date = new Date(parseInt(ts, 10));
  return date.toLocaleDateString();
}

export function ExperimentList({
  experiments,
  selectedId,
  onSelect,
  loading,
}: Props) {
  if (loading) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        Loading experiments...
      </div>
    );
  }

  if (experiments.length === 0) {
    return (
      <div className="p-4 text-sm text-muted-foreground">
        No experiments found in MLflow.
      </div>
    );
  }

  return (
    <div className="space-y-1">
      {experiments.map((exp) => (
        <button
          key={exp.experiment_id}
          onClick={() => onSelect(exp.experiment_id)}
          className={`w-full text-left rounded-md px-3 py-2.5 transition-colors ${
            selectedId === exp.experiment_id
              ? "bg-primary/10 text-primary border border-primary/30"
              : "hover:bg-muted border border-transparent"
          }`}
        >
          <div className="flex items-center gap-2">
            <FlaskConical className="h-3.5 w-3.5 shrink-0" />
            <span className="text-sm font-medium truncate">{exp.name}</span>
          </div>
          <div className="mt-1 flex items-center justify-between text-[10px] text-muted-foreground pl-5">
            <span>{exp.run_count} runs</span>
            <span>{formatTimestamp(exp.latest_run_time)}</span>
          </div>
        </button>
      ))}
    </div>
  );
}
