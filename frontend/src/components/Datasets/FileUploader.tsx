import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Upload, Loader2, CheckCircle } from "lucide-react";
import { uploadImageToDataset } from "@/lib/inspection/apiClient";

interface Props {
  datasetId: string;
  onComplete: () => void;
}

export function FileUploader({ datasetId, onComplete }: Props) {
  const [file, setFile] = useState<File | null>(null);
  const [split, setSplit] = useState("train");
  const [uploading, setUploading] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    try {
      await uploadImageToDataset(datasetId, file, split);
      setSuccess(true);
      setFile(null);
      onComplete();
      setTimeout(() => setSuccess(false), 2000);
    } catch (err: any) {
      alert(err.message);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-end gap-4">
        <div className="flex-1 space-y-1.5">
          <label className="text-sm font-medium">Select Image</label>
          <input
            type="file"
            accept="image/*"
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

      <Button
        onClick={handleUpload}
        disabled={!file || uploading || success}
        className="w-full"
      >
        {uploading ? (
          <><Loader2 className="h-4 w-4 mr-2 animate-spin" /> Uploading...</>
        ) : success ? (
          <><CheckCircle className="h-4 w-4 mr-2" /> Uploaded Successfully</>
        ) : (
          <><Upload className="h-4 w-4 mr-2" /> Upload to {split}</>
        )}
      </Button>
    </div>
  );
}
