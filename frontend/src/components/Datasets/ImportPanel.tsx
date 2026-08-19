import { ZipUploader } from "./ZipUploader";

interface Props {
  datasetId: string;
  onImportComplete: () => void;
}

export function ImportPanel({ datasetId, onImportComplete }: Props) {
  return (
    <div className="rounded-lg border border-border bg-card p-5 space-y-4">
      <h3 className="text-base font-semibold flex items-center gap-2">Import Images</h3>
      <ZipUploader datasetId={datasetId} onComplete={onImportComplete} />
    </div>
  );
}
