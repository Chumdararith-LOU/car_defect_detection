import { useEffect, useState, useRef } from "react";
import type { TrainingJob } from "@/lib/inspection/trainingSchema";
import {
  fetchTrainingJobDetail,
  fetchTrainingJobLogs,
  stopTrainingJob,
} from "@/lib/inspection/apiClient";
import { Button } from "@/components/ui/button";
import { Loader2, Square, ArrowLeft, RefreshCw } from "lucide-react";

interface Props {
  jobId: string;
  onBack: () => void;
}

const STATUS_STYLES: Record<string, string> = {
  pending: "bg-gray-500/15 text-gray-700 dark:text-gray-400 border-gray-500/30",
  running: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30",
  completed: "bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/30",
  failed: "bg-red-500/15 text-red-700 dark:text-red-400 border-red-500/30",
  cancelled: "bg-yellow-500/15 text-yellow-700 dark:text-yellow-400 border-yellow-500/30",
};

export function JobDetailPanel({ jobId, onBack }: Props) {
  const [job, setJob] = useState<TrainingJob | null>(null);
  const [logs, setLogs] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const logEndRef = useRef<HTMLDivElement>(null);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [jobDetail, jobLogs] = await Promise.all([
        fetchTrainingJobDetail(jobId),
        fetchTrainingJobLogs(jobId),
      ]);
      setJob(jobDetail);
      setLogs(jobLogs);
    } catch (err: any) {
      setError(err.message || "Failed to load job details");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // Poll every 3 seconds if job is active
    const interval = setInterval(() => {
      if (job && (job.status === "running" || job.status === "pending")) {
        loadData();
      }
    }, 3000);

    return () => clearInterval(interval);
  }, [jobId, job?.status]);

  useEffect(() => {
    if (logEndRef.current) {
      logEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [logs]);

  const handleStop = async () => {
    if (!window.confirm("Are you sure you want to terminate this training job?")) return;
    try {
      await stopTrainingJob(jobId);
      loadData();
    } catch (err: any) {
      alert(`Failed to stop job: ${err.message}`);
    }
  };

  if (loading && !job) {
    return (
      <div className="p-8 text-center text-muted-foreground">
        Loading job details...
      </div>
    );
  }

  if (error) {
    return <div className="p-8 text-center text-destructive">Error: {error}</div>;
  }

  if (!job) return null;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1"
        >
          <ArrowLeft className="h-4 w-4" /> Back to jobs
        </button>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={loadData}>
            <RefreshCw className="h-4 w-4 mr-1.5" /> Refresh
          </Button>
          {(job.status === "running" || job.status === "pending") && (
            <Button variant="destructive" size="sm" onClick={handleStop}>
              <Square className="h-4 w-4 mr-1.5" /> Stop Job
            </Button>
          )}
        </div>
      </div>

      {/* Job Metadata Card */}
      <div className="rounded-lg border border-border bg-card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-semibold font-mono">
            {job.project_name} / {job.run_name}
          </h2>
          <span
            className={`px-2 py-0.5 rounded-full text-xs font-medium border capitalize ${
              STATUS_STYLES[job.status] || STATUS_STYLES.pending
            }`}
          >
            {job.status}
          </span>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">Stage</p>
            <p className="font-medium capitalize">{job.stage}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Device</p>
            <p className="font-medium">{job.device}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Created</p>
            <p className="font-medium">
              {new Date(job.created_at).toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Dataset</p>
            <p className="font-medium truncate" title={job.dataset_path}>
              {job.dataset_path.split("/").pop()}
            </p>
          </div>
        </div>
        {job.error_message && (
          <div className="rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-700 dark:text-red-400">
            <strong>Error:</strong> {job.error_message}
          </div>
        )}
      </div>

      {/* Logs Viewer */}
      <div className="rounded-lg border border-border bg-black/90 text-green-400 font-mono text-xs overflow-hidden">
        <div className="bg-black/50 px-4 py-2 border-b border-white/10 text-gray-300 flex items-center justify-between">
          <span>Training Logs</span>
          {job.status === "running" && <Loader2 className="h-3 w-3 animate-spin" />}
        </div>
        <div className="p-4 h-[500px] overflow-y-auto whitespace-pre-wrap break-words">
          {logs || "No logs available yet..."}
          <div ref={logEndRef} />
        </div>
      </div>
    </div>
  );
}
