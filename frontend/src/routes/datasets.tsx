import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { fetchDatasets, fetchDatasetDetail } from "@/lib/inspection/apiClient";
import type { DatasetSummary, DatasetDetail } from "@/lib/inspection/schema";
import {
  DatasetListView,
  DatasetDetailPanel,
  ReviewToDatasetBuilder,
  NewDatasetDialog,
} from "@/components/Datasets";
import { Button } from "@/components/ui/button";
import { Hammer, Plus, Upload } from "lucide-react";

export const Route = createFileRoute("/datasets")({
  component: DatasetsPage,
});

type ViewMode = "list" | "detail" | "builder";

function DatasetsPage() {
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [selectedDetail, setSelectedDetail] = useState<DatasetDetail | null>(
    null,
  );
  const [showNewDialog, setShowNewDialog] = useState(false);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>("list");

  const loadDatasets = async () => {
    try {
      setLoading(true);
      const res = await fetchDatasets();
      setDatasets(res.datasets);
    } catch (err: any) {
      setError(err.message || "Failed to load datasets");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadDatasets();
  }, []);

  const handleSelect = async (datasetId: string) => {
    try {
      setDetailLoading(true);
      const detail = await fetchDatasetDetail(datasetId);
      setSelectedDetail(detail);
      setViewMode("detail");
    } catch (err: any) {
      setError(err.message || "Failed to load dataset detail");
    } finally {
      setDetailLoading(false);
    }
  };

  const handleBack = () => {
    setSelectedDetail(null);
    setViewMode("list");
  };

  const handleOpenBuilder = () => {
    setSelectedDetail(null);
    setViewMode("builder");
  };

  const handleBackFromBuilder = () => {
    setViewMode("list");
  };

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-2xl font-semibold tracking-tight">
            Dataset Management
          </h1>
          <p className="text-sm text-muted-foreground mt-1">
            Engineer workspace. List dataset versions, audit leakage, and build
            new datasets from the data flywheel.
          </p>
        </div>
        {!selectedDetail && (
          <div className="flex gap-2">
            <Button variant="outline" size="sm" onClick={handleOpenBuilder}>
              <Hammer className="h-4 w-4 mr-1.5" />
              Build from Reviews
            </Button>
            <Button size="sm" onClick={() => setShowNewDialog(true)}>
              <Plus className="h-4 w-4 mr-1.5" />
              New Dataset
            </Button>
          </div>
        )}
      </div>

      {loading && (
        <div className="rounded-lg border border-border bg-card p-8 text-center text-muted-foreground">
          Loading datasets...
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-border bg-card p-8 text-center text-destructive">
          Error: {error}
        </div>
      )}

      {detailLoading && (
        <div className="rounded-lg border border-border bg-card p-8 text-center text-muted-foreground">
          Loading dataset detail...
        </div>
      )}

      {!loading && !error && !detailLoading && viewMode === "builder" && (
        <ReviewToDatasetBuilder onBack={handleBackFromBuilder} />
      )}

      {!loading &&
        !error &&
        !detailLoading &&
        viewMode === "detail" &&
        selectedDetail && (
          <DatasetDetailPanel
            dataset={selectedDetail}
            onBack={handleBack}
            onDeleted={() => {
              setSelectedDetail(null);
              setViewMode("list");
              loadDatasets(); // Refresh the list
            }}
          />
        )}

      {!loading && !error && !detailLoading && !selectedDetail && (
        <DatasetListView datasets={datasets} onSelect={handleSelect} />
      )}
      {showNewDialog && (
        <NewDatasetDialog
          onClose={() => setShowNewDialog(false)}
          onCreated={loadDatasets}
        />
      )}
    </div>
  );
}
