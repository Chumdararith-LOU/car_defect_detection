import type { TrainingJob, TrainingStatus } from "@/lib/inspection/trainingSchema";
import { Button } from "@/components/ui/button";
import { EmptyState, StatusBadge } from "@/components/Shared";
import type { BadgeTone } from "@/components/Shared";
import { Loader2, Square, FileText } from "lucide-react";

interface Props {
  jobs: TrainingJob[];
  loading: boolean;
  onSelectJob: (job: TrainingJob) => void;
  onStopJob: (jobId: string) => void;
}

const STATUS_TONES: Record<TrainingStatus, BadgeTone> = {
  pending: "gray",
  running: "blue",
  completed: "green",
  failed: "red",
  cancelled: "yellow",
};

function formatDate(iso: string | null): string {
  if (!iso) return "-";
  return new Date(iso).toLocaleString();
}

export function JobListTable({ jobs, loading, onSelectJob, onStopJob }: Props) {
  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 text-muted-foreground">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading jobs...
      </div>
    );
  }

  if (jobs.length === 0) {
    return <EmptyState title="No training jobs found" hint="Launch one to get started." />;
  }

  return (
    <div className="overflow-x-auto rounded-lg border border-border">
      <table className="w-full text-sm">
        <thead className="bg-muted/50 text-xs uppercase tracking-wider text-muted-foreground">
          <tr>
            <th className="px-4 py-3 text-left font-medium">ID</th>
            <th className="px-4 py-3 text-left font-medium">Stage</th>
            <th className="px-4 py-3 text-left font-medium">Status</th>
            <th className="px-4 py-3 text-left font-medium">Project / Run</th>
            <th className="px-4 py-3 text-left font-medium">Created</th>
            <th className="px-4 py-3 text-right font-medium">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border bg-card">
          {jobs.map((job) => (
            <tr
              key={job.id}
              className="hover:bg-muted/30 transition-colors cursor-pointer"
              onClick={() => onSelectJob(job)}
            >
              <td className="px-4 py-3 font-mono text-xs">{job.id.substring(0, 8)}...</td>
              <td className="px-4 py-3 capitalize">{job.stage}</td>
              <td className="px-4 py-3">
                <StatusBadge
                  tone={STATUS_TONES[job.status]}
                  size="md"
                  icon={
                    job.status === "running" ? (
                      <Loader2 className="h-3 w-3 animate-spin" />
                    ) : undefined
                  }
                >
                  {job.status}
                </StatusBadge>
              </td>
              <td className="px-4 py-3">
                <div className="font-medium">{job.project_name}</div>
                <div className="text-xs text-muted-foreground">{job.run_name}</div>
              </td>
              <td className="px-4 py-3 text-xs text-muted-foreground">
                {formatDate(job.created_at)}
              </td>
              <td className="px-4 py-3 text-right">
                <div className="flex justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onSelectJob(job)}
                    title="View Logs"
                  >
                    <FileText className="h-4 w-4" />
                  </Button>
                  {job.status === "running" || job.status === "pending" ? (
                    <Button
                      variant="destructive"
                      size="sm"
                      onClick={() => onStopJob(job.id)}
                      title="Stop Job"
                    >
                      <Square className="h-4 w-4" />
                    </Button>
                  ) : null}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
