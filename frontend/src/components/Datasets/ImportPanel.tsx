import { useState } from "react";
import { Database, Archive } from "lucide-react";
import { InspectionPicker } from "./InspectionPicker";
import { ZipUploader } from "./ZipUploader";

interface Props {
  datasetId: string;
  onImportComplete: () => void;
}

export function ImportPanel({ datasetId, onImportComplete }: Props) {
  const [mode, setMode] = useState<"flywheel" | "zip">("flywheel");
  return (
    <div className="rounded-lg border border-border bg-card p-5 space-y-4">
      <h3 className="text-base font-semibold flex items-center gap-2">
        Import Images
      </h3>

      <div className="flex gap-2 border-b border-border pb-2">
        <button
          onClick={() => setMode("flywheel")}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-t-md transition-colors ${
            mode === "flywheel"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted"
          }`}
        >
          <Database className="h-4 w-4" /> From Flywheel
        </button>
        <button
          onClick={() => setMode("zip")}
          className={`flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-t-md transition-colors ${
            mode === "zip"
              ? "bg-primary text-primary-foreground"
              : "text-muted-foreground hover:bg-muted"
          }`}
        >
          <Archive className="h-4 w-4" /> Upload ZIP
        </button>
      </div>

      {mode === "flywheel" && (
        <InspectionPicker datasetId={datasetId} onComplete={onImportComplete} />
      )}
      {mode === "zip" && (
        <ZipUploader datasetId={datasetId} onComplete={onImportComplete} />
      )}
    </div>
  );
}
