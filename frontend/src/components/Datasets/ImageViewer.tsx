import { useEffect, useState } from "react";
import { X, Eye, EyeOff, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import type { DatasetImageAnnotation } from "@/lib/inspection/schema";
import {
  fetchDatasetImageLabels,
  getDatasetImageUrl,
  reclassifyAnnotation,
  deleteAnnotation,
} from "@/lib/inspection/apiClient";
import { MaskOverlay } from "./MaskOverlay";
import { ReclassifyDialog } from "./ReclassifyDialog";

interface Props {
  datasetId: string;
  filename: string;
  onClose: () => void;
}

export function ImageViewer({ datasetId, filename, onClose }: Props) {
  const [annotations, setAnnotations] = useState<DatasetImageAnnotation[]>([]);
  const [classNames, setClassNames] = useState<string[]>([]);
  const [showMasks, setShowMasks] = useState(true);
  const [imgDims, setImgDims] = useState({ width: 800, height: 600 });
  const [reclassifyIndex, setReclassifyIndex] = useState<number | null>(null);

  const loadLabels = () => {
    fetchDatasetImageLabels(datasetId, filename)
      .then((res) => {
        setAnnotations(res.annotations);
        setClassNames(res.class_names || []);
      })
      .catch((err) => console.error(err));
  };

  useEffect(() => {
    loadLabels();
  }, [datasetId, filename]);

  const handleImageLoad = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    setImgDims({ width: img.naturalWidth, height: img.naturalHeight });
  };

  const imageUrl = getDatasetImageUrl(datasetId, filename);

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-8"
      onClick={onClose}
    >
      <div
        className="relative flex max-h-full max-w-5xl flex-col overflow-hidden rounded-lg bg-card shadow-2xl border border-border"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between border-b border-border p-3">
          <h3 className="font-mono text-sm font-medium truncate">{filename}</h3>
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowMasks(!showMasks)}
            >
              {showMasks ? (
                <EyeOff className="h-4 w-4 mr-1" />
              ) : (
                <Eye className="h-4 w-4 mr-1" />
              )}
              {showMasks ? "Hide Masks" : "Show Masks"}
            </Button>
            <Button variant="ghost" size="icon" onClick={onClose}>
              <X className="h-5 w-5" />
            </Button>
          </div>
        </div>

        {/* Image + Overlay */}
        <div className="relative flex-1 overflow-auto bg-muted/20 p-4 flex items-center justify-center">
          <div className="relative inline-block">
            <img
              src={imageUrl}
              alt={filename}
              onLoad={handleImageLoad}
              className="max-h-[70vh] w-auto rounded shadow-lg"
            />
            <MaskOverlay
              annotations={annotations}
              width={imgDims.width}
              height={imgDims.height}
              visible={showMasks}
            />
          </div>
        </div>

        {/* Footer Legend */}
        <div className="border-t border-border p-3 flex flex-wrap items-center gap-2 text-xs">
          <span className="text-muted-foreground font-medium">
            Annotations ({annotations.length}):
          </span>
          {annotations.map((ann) => (
            <span
              key={ann.index}
              className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-muted font-mono"
            >
              {ann.class_name}
              <button
                onClick={() => setReclassifyIndex(ann.index)}
                className="text-muted-foreground hover:text-blue-500 transition-colors"
                title="Reclassify"
              >
                <Pencil className="h-3 w-3" />
              </button>
              <button
                onClick={async () => {
                  if (
                    !confirm(
                      `Delete this ${ann.class_name} annotation? (False Positive)`,
                    )
                  )
                    return;
                  try {
                    await deleteAnnotation(datasetId, filename, ann.index);
                    loadLabels(); // Refresh annotations
                  } catch (err: any) {
                    alert(err.message);
                  }
                }}
                className="text-muted-foreground hover:text-red-500 transition-colors"
                title="Delete annotation (False Positive)"
              >
                <Trash2 className="h-3 w-3" />
              </button>
            </span>
          ))}
        </div>

        {/* Reclassify Dialog */}
        {reclassifyIndex !== null && classNames.length > 0 && (
          <ReclassifyDialog
            classNames={classNames}
            currentClassId={
              annotations.find((a) => a.index === reclassifyIndex)?.class_id ??
              0
            }
            onConfirm={async (newClassId) => {
              await reclassifyAnnotation(
                datasetId,
                filename,
                reclassifyIndex,
                newClassId,
              );
              setReclassifyIndex(null);
              loadLabels(); // Refresh annotations
            }}
            onCancel={() => setReclassifyIndex(null)}
          />
        )}
      </div>
    </div>
  );
}
