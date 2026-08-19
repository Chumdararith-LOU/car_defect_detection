import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DatasetDetail } from "@/lib/inspection/schema";
import { ClassDistributionBar } from "./ClassDistributionBar";
import { LeakageAuditPanel } from "./LeakageAuditPanel";
import { ImageGallery } from "./ImageGallery";
import { Award, Folder, Image, Layers, Trash2 } from "lucide-react";
import { ImportPanel } from "./ImportPanel";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { ConfirmDialog } from "@/components/Shared";
import {
  deleteDataset,
  fetchDatasetAuditReport,
  runFullDatasetAudit,
} from "@/lib/inspection/apiClient";
import type { AuditReport } from "@/lib/inspection/platformSchema";
import { DatasetAuditReport } from "./DatasetAuditReport";
import { Button } from "@/components/ui/button";
import { DatasetPrepPanel } from "./DatasetPrepPanel";

interface Props {
  dataset: DatasetDetail;
  onBack: () => void;
  onDeleted: () => void;
  onDatasetChanged?: () => void;
}

export function DatasetDetailPanel({ dataset, onBack, onDeleted, onDatasetChanged }: Props) {
  const [galleryKey, setGalleryKey] = useState(0);
  const [auditReport, setAuditReport] = useState<AuditReport | null>(null);
  const [auditLoading, setAuditLoading] = useState(true);
  const [auditRunning, setAuditRunning] = useState(false);
  const [auditError, setAuditError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    fetchDatasetAuditReport(dataset.dataset_id)
      .then((r) => {
        if (!cancelled) setAuditReport(r);
      })
      .catch((e) => {
        if (!cancelled) setAuditError(e instanceof Error ? e.message : "Failed to load audit");
      })
      .finally(() => {
        if (!cancelled) setAuditLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [dataset.dataset_id]);

  const handleRunAudit = async () => {
    setAuditRunning(true);
    setAuditError(null);
    try {
      const r = await runFullDatasetAudit(dataset.dataset_id);
      setAuditReport(r);
    } catch (e) {
      setAuditError(e instanceof Error ? e.message : "Audit failed");
    } finally {
      setAuditRunning(false);
    }
  };

  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const handleDelete = async () => {
    try {
      await deleteDataset(dataset.dataset_id);
      toast.success("Dataset deleted");
      onDeleted();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to delete dataset");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <button
          onClick={onBack}
          className="text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          ← Back to list
        </button>
        <Button
          variant="destructive"
          size="sm"
          onClick={() => setShowDeleteConfirm(true)}
          className="flex items-center gap-1.5"
        >
          <Trash2 className="h-3.5 w-3.5" />
          Delete Dataset
        </Button>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg flex items-center gap-2">
              {dataset.name}
              {dataset.is_champion && (
                <span className="flex items-center gap-1 text-xs font-normal bg-yellow-500/15 text-yellow-700 dark:text-yellow-400 px-2 py-0.5 rounded-full border border-yellow-500/30">
                  <Award className="h-3 w-3" /> Champion
                </span>
              )}
            </CardTitle>
            <span className="text-xs font-mono text-muted-foreground">{dataset.dataset_id}</span>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="space-y-1">
              <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                <Image className="h-3 w-3" /> Total Images
              </p>
              <p className="text-xl font-semibold">{dataset.total_images.toLocaleString()}</p>
            </div>
            <div className="space-y-1">
              <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                <Layers className="h-3 w-3" /> Classes
              </p>
              <p className="text-xl font-semibold">{dataset.nc}</p>
            </div>
            <div className="space-y-1">
              <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-1">
                <Folder className="h-3 w-3" /> Root Path
              </p>
              <p className="text-xs font-mono truncate" title={dataset.root_path}>
                {dataset.root_path.split("/").slice(-2).join("/")}
              </p>
            </div>
            <div className="space-y-1">
              <p className="text-[10px] font-mono uppercase tracking-wider text-muted-foreground">
                Status
              </p>
              <p className="text-sm font-medium capitalize">{dataset.status}</p>
            </div>
          </div>

          {/* Class Distribution */}
          <div className="space-y-2">
            <h4 className="text-sm font-semibold">Class Distribution</h4>
            <ClassDistributionBar distribution={dataset.class_distribution} />
          </div>
        </CardContent>
      </Card>

      {/* Dataset Preparation */}
      <DatasetPrepPanel
        datasetId={dataset.dataset_id}
        datasetName={dataset.name}
        totalImages={dataset.total_images}
        onPrepComplete={() => {
          setGalleryKey((k) => k + 1);
          onDatasetChanged?.();
        }}
      />

      {/* Leakage Audit */}
      <LeakageAuditPanel datasetId={dataset.dataset_id} />
      {/* Training Readiness Audit */}
      <DatasetAuditReport
        report={auditReport}
        loading={auditLoading}
        running={auditRunning}
        error={auditError}
        onRun={handleRunAudit}
      />

      {/* Import Tools */}
      <ImportPanel
        datasetId={dataset.dataset_id}
        onImportComplete={() => {
          setGalleryKey((k) => k + 1);
          onDatasetChanged?.();
        }}
      />

      {/* Image Browser */}
      <div className="space-y-3">
        <h3 className="text-lg font-semibold flex items-center gap-2">
          Browse Images ({dataset.total_images.toLocaleString()})
        </h3>
        <ImageGallery datasetId={dataset.dataset_id} key={galleryKey} />
      </div>
      <ConfirmDialog
        open={showDeleteConfirm}
        onOpenChange={setShowDeleteConfirm}
        title="Delete dataset?"
        description={`'${dataset.name}' and all its images, labels, and configurations will be permanently deleted. This cannot be undone.`}
        confirmLabel="Delete Dataset"
        onConfirm={handleDelete}
      />
    </div>
  );
}
