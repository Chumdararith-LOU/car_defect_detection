import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Archive, Loader2, CheckCircle } from "lucide-react";
import { importZipToDataset } from "@/lib/inspection/apiClient";

interface Props {
  datasetId: string;
  onComplete: () => void;
}

export function ZipUploader({ datasetId, onComplete }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [split, setSplit] = useState("train");
  const [uploading, setUploading] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const res = await importZipToDataset(datasetId, file, split);
      setSuccessMsg(res.message);
      setFile(null);
      onComplete();
    } catch (err: any) {
      setError(err.message || "Upload failed");
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <p className="text-xs text-muted-foreground">
        Upload a ZIP archive containing image files (<code>.jpg</code>, <code>.png</code>) and their corresponding YOLO label files (<code>.txt</code>).
      </p>
      <div className="flex items-end gap-4">
        <div className="flex-1 space-y-1.5">
          <label className="text-sm font-medium">Select ZIP Archive</label>
          <input
            type="file"
            accept=".zip,application/zip"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
          />
        </div>
        <div className="space-y-1.5">
          <label className="text-sm font-medium">Split</label>
          <select
            value={split}
            onChange={(e) => setSplit(e.target.value)}
            className="block w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
          >
            <option value="train">train</option>
            <option value="val">val</option>
            <option value="test">test</option>
          </select>
        </div>
      </div>

      {error && <p className="text-xs text-destructive">{error}</p>}
      {successMsg && <p className="text-xs text-green-600 dark:text-green-400 flex items-center gap-1"><CheckCircle className="h-3.5 w-3.5" /> {successMsg}</p>}

      <Button
        onClick={handleUpload}
        disabled={!file || uploading}
        className="w-full"
      >
        {uploading ? (
          <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Extracting & Importing...</>
        ) : (
          <><Archive className="h-4 w-4 mr-2" /> Import ZIP to {split}</>
        )}
      </Button>
    </div>
  );
}
