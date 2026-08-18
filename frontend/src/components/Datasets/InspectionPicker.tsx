import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, CheckCircle } from "lucide-react";
import type { SavedInspection } from "@/lib/inspection/schema";
import { fetchAvailableInspections, importInspectionToDataset } from "@/lib/inspection/apiClient";

interface Props {
  datasetId: string;
  onComplete: () => void;
}

export function InspectionPicker({ datasetId, onComplete }: Props) {
  const [inspections, setInspections] = useState<SavedInspection[]>([]);
  const [loading, setLoading] = useState(true);
  const [importingId, setImportingId] = useState<string | null>(null);
  const [successId, setSuccessId] = useState<string | null>(null);
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
      await importInspectionToDataset(datasetId, inspectionId, split);
      setSuccessId(inspectionId);
      setTimeout(() => setSuccessId(null), 2000);
      onComplete();
    } catch (err: any) {
      alert(err.message);
    } finally {
      setImportingId(null);
    }
  };

  if (loading) return <p className="text-sm text-muted-foreground">Loading saved inspections...</p>;
  if (inspections.length === 0) return <p className="text-sm text-muted-foreground">No saved inspections found. Run an inspection first.</p>;

  return (
    <div className="space-y-3">
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
          <div key={insp.inspection_id} className="flex items-center justify-between p-3 text-sm hover:bg-muted/30">
            <div>
              <p className="font-mono text-xs font-medium">{insp.inspection_id}</p>
              <p className="text-xs text-muted-foreground">
                {insp.defect_count} defects • {insp.inspection_status} • {new Date(insp.timestamp).toLocaleDateString()}
              </p>
            </div>
            <Button
              size="sm"
              variant={successId === insp.inspection_id ? "default" : "outline"}
              onClick={() => handleImport(insp.inspection_id)}
              disabled={importingId !== null || successId === insp.inspection_id}
            >
              {importingId === insp.inspection_id ? (
                <><Loader2 className="h-3 w-3 mr-1 animate-spin" /> Importing...</>
              ) : successId === insp.inspection_id ? (
                <><CheckCircle className="h-3 w-3 mr-1" /> Imported</>
              ) : (
                "Import"
              )}
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
