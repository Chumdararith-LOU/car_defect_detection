import { useState, type ChangeEvent } from "react";
import { Button } from "@/components/ui/button";
import { Loader2, Upload, X } from "lucide-react";
import type { DatasetStage } from "@/lib/inspection/schema";
import { createNewDataset, importDatasetZip } from "@/lib/inspection/apiClient";
import type { ImportDatasetResponse } from "@/lib/inspection/prepSchema";
import { SplitStructurePanel } from "./SplitStructurePanel";

interface Props {
  onClose: () => void;
  onCreated: () => void;
}

type Tab = "empty" | "zip";

export function NewDatasetDialog({ onClose, onCreated }: Props) {
  const [activeTab, setActiveTab] = useState<Tab>("empty");
  const [error, setError] = useState<string | null>(null);

  // --- Empty Tab State ---
  const [versionName, setVersionName] = useState("");
  const [stage, setStage] = useState<DatasetStage>("stage2");
  const [notes, setNotes] = useState("");
  const [creating, setCreating] = useState(false);

  // --- ZIP Tab State ---
  const [zipName, setZipName] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportDatasetResponse | null>(null);

  const handleCreateEmpty = async () => {
    if (!versionName.trim()) return;
    setCreating(true);
    setError(null);
    try {
      await createNewDataset(versionName.trim(), stage, notes || null);
      onCreated();
      onClose();
    } catch (err: any) {
      setError(err.message || "Failed to create dataset");
    } finally {
      setCreating(false);
    }
  };

  const handleImportZip = async () => {
    if (!zipName.trim() || !selectedFile) return;
    setImporting(true);
    setError(null);
    try {
      const res = await importDatasetZip(selectedFile, zipName.trim());
      setImportResult(res);
      onCreated();
    } catch (err: any) {
      setError(err.message || "Failed to import dataset");
    } finally {
      setImporting(false);
    }
  };

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    setSelectedFile(e.target.files?.[0] ?? null);
    setError(null);
  };

  // --- Phase 2: ZIP Import Result View ---
  if (importResult) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
        <div className="w-full max-w-lg space-y-4 rounded-lg border border-border bg-card p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold">Imported: {importResult.dataset_id}</h3>
            <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
              <X className="h-5 w-5" />
            </button>
          </div>
          <p className="text-sm text-muted-foreground">{importResult.message}</p>
          <SplitStructurePanel structure={importResult.structure} />
          <div className="flex justify-end">
            <Button onClick={onClose}>Done</Button>
          </div>
        </div>
      </div>
    );
  }

  // --- Phase 1: Tabs Form View ---
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50" onClick={onClose}>
      <div className="w-full max-w-md space-y-4 rounded-lg border border-border bg-card p-6 shadow-xl" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold">New Dataset</h3>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Tabs */}
        <div className="flex gap-2 border-b border-border pb-2">
          <button
            onClick={() => { setActiveTab("empty"); setError(null); }}
            className={`px-3 py-1.5 text-sm font-medium rounded-t-md transition-colors ${
              activeTab === "empty" ? "bg-muted text-foreground border-b-2 border-primary" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            Empty Dataset
          </button>
          <button
            onClick={() => { setActiveTab("zip"); setError(null); }}
            className={`px-3 py-1.5 text-sm font-medium rounded-t-md transition-colors ${
              activeTab === "zip" ? "bg-muted text-foreground border-b-2 border-primary" : "text-muted-foreground hover:text-foreground"
            }`}
          >
            From YOLO ZIP
          </button>
        </div>

        {/* Empty Tab Content */}
        {activeTab === "empty" && (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Version Name</label>
              <input type="text" value={versionName} onChange={(e) => setVersionName(e.target.value)} placeholder="e.g. v4.0_expanded" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Stage</label>
              <select value={stage} onChange={(e) => setStage(e.target.value as DatasetStage)} className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm">
                <option value="stage1">Stage 1 (SOD / Anomaly)</option>
                <option value="stage2">Stage 2 (7-class defect)</option>
                <option value="stage3">Stage 3 (21-class panel)</option>
              </select>
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Notes (optional)</label>
              <textarea value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Purpose..." className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[60px]" />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={onClose}>Cancel</Button>
              <Button onClick={handleCreateEmpty} disabled={!versionName.trim() || creating}>
                {creating ? <><Loader2 className="h-4 w-4 mr-1.5 animate-spin" /> Creating...</> : "Create Empty"}
              </Button>
            </div>
          </div>
        )}

        {/* ZIP Tab Content */}
        {activeTab === "zip" && (
          <div className="space-y-3">
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Version Name</label>
              <input type="text" value={zipName} onChange={(e) => setZipName(e.target.value)} placeholder="e.g. yolo_seg_clean_2200" className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm" />
            </div>
            <div className="space-y-1.5">
              <label className="text-sm font-medium">Dataset ZIP</label>
              <label className="flex w-full cursor-pointer items-center justify-center gap-2 rounded-md border border-dashed border-input bg-background px-3 py-6 text-sm text-muted-foreground transition-colors hover:border-foreground/40">
                <Upload className="h-4 w-4" />
                <span>{selectedFile ? selectedFile.name : "Click to select a .zip file"}</span>
                <input type="file" accept=".zip" onChange={handleFileChange} className="hidden" />
              </label>
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" onClick={onClose}>Cancel</Button>
              <Button onClick={handleImportZip} disabled={!zipName.trim() || !selectedFile || importing}>
                {importing ? <><Loader2 className="h-4 w-4 mr-1.5 animate-spin" /> Importing...</> : "Import ZIP"}
              </Button>
            </div>
          </div>
        )}

        {error && <p className="text-xs text-destructive">{error}</p>}
      </div>
    </div>
  );
}
