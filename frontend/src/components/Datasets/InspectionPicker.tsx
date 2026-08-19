import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle, Trash2 } from "lucide-react";
import { toast } from "sonner";
import type { SavedInspection } from "@/lib/inspection/schema";
import {
  fetchAvailableInspections,
  importInspectionToDataset,
  deleteInspection,
  getInspectionImageUrl,
} from "@/lib/inspection/apiClient";

interface Props {
  datasetId: string;
  datasetName?: string;
  onComplete: () => void;
}

export function InspectionPicker({ datasetId, datasetName, onComplete }: Props) {
  const [inspections, setInspections] = useState<SavedInspection[]>([]);
  const [loading, setLoading] = useState(true);
  const [importingId, setImportingId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [importedIds, setImportedIds] = useState<Set<string>>(new Set());
  const [split, setSplit] = useState("train");

  useEffect(() => {
    fetchAvailableInspections()
      .then((res) => setInspections(res.inspections))
      .catch((err) => console.error(err))
      .finally(() => setLoading(false));
  }, []);

  const handleImport = async (inspectionId: string) => {
    setImportingId(inspectionId);
    try {
      const result = await importInspectionToDataset(datasetId, inspectionId, split);
      const labels = (result as { labels_written?: number }).labels_written ?? 0;
      const skipped = (result as { skipped_classes?: string[] }).skipped_classes ?? [];
      setImportedIds((prev) => new Set(prev).add(inspectionId));
      toast.success(
        `Imported ${inspectionId} into ${datasetName ?? datasetId} (${split}) — ${labels} labels written`,
      );
      if (skipped.length > 0) {
        toast.warning(
          `Taxonomy mismatch: skipped ${skipped.join(", ")} (not in ${datasetName ?? datasetId})`,
        );
      }
      onComplete();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      toast.error(message);
    } finally {
      setImportingId(null);
    }
  };

  const handleDelete = async (inspectionId: string) => {
    setDeletingId(inspectionId);
    try {
      await deleteInspection(inspectionId);
      setInspections((prev) => prev.filter((i) => i.inspection_id !== inspectionId));
      toast.success("Inspection deleted");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : String(err);
      toast.error(message);
    } finally {
      setDeletingId(null);
    }
  };

  if (loading) return <p className="text-sm text-muted-foreground">Loading saved inspections...</p>;
  if (inspections.length === 0)
    return (
      <p className="text-sm text-muted-foreground">
        No saved inspections found. Run an inspection first.
      </p>
    );

  return (
    <div className="space-y-3">
      <div className="rounded-md border border-primary/30 bg-primary/10 px-3 py-2 text-xs">
        Importing into: <span className="font-mono font-semibold">{datasetName ?? datasetId}</span>
      </div>
      <div className="flex items-center gap-2 text-sm">
        <label className="font-medium">Target Split:</label>
        <select
          value={split}
          onChange={(e) => setSplit(e.target.value)}
          className="rounded border border-input bg-background px-2 py-1 text-xs"
        >
          <option value="train">train</option>
          <option value="val">val</option>
          <option value="test">test</option>
        </select>
      </div>

      <div className="max-h-64 overflow-y-auto rounded border border-border divide-y divide-border">
        {inspections.map((insp) => (
          <div
            key={insp.inspection_id}
            className="flex items-center justify-between p-3 text-sm hover:bg-muted/30"
          >
            <div className="flex min-w-0 items-center gap-3">
              <img
                src={getInspectionImageUrl(insp.inspection_id)}
                alt={insp.inspection_id}
                loading="lazy"
                className="h-10 w-14 shrink-0 rounded border border-border object-cover"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.visibility = "hidden";
                }}
              />
              <div className="min-w-0">
                <p className="font-mono text-xs font-medium truncate">{insp.inspection_id}</p>
                <p className="text-xs text-muted-foreground">
                  {insp.defect_count} defects • {insp.inspection_status} •{" "}
                  {new Date(insp.timestamp).toLocaleDateString()}
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Button
                size="sm"
                variant="ghost"
                className="text-destructive hover:text-destructive h-8 w-8 p-0"
                onClick={() => handleDelete(insp.inspection_id)}
                disabled={deletingId !== null || importingId !== null}
                title="Delete inspection"
              >
                {deletingId === insp.inspection_id ? (
                  <Loader2 className="h-3 w-3 animate-spin" />
                ) : (
                  <Trash2 className="h-3 w-3" />
                )}
              </Button>
              <Button
                size="sm"
                variant={importedIds.has(insp.inspection_id) ? "default" : "outline"}
                onClick={() => handleImport(insp.inspection_id)}
                disabled={importingId !== null || importedIds.has(insp.inspection_id)}
              >
                {importingId === insp.inspection_id ? (
                  <>
                    <Loader2 className="h-3 w-3 mr-1 animate-spin" /> Importing...
                  </>
                ) : importedIds.has(insp.inspection_id) ? (
                  <>
                    <CheckCircle className="h-3 w-3 mr-1" /> Imported
                  </>
                ) : (
                  "Import"
                )}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
