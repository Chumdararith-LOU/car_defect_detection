import type {
  Defect,
  SuppressedDetection,
  UnclassifiedAnomaly,
} from "@/lib/inspection/schema";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AnomalyCard } from "./AnomalyCard";
import { DefectCard } from "./DefectCard";
import { SuppressedCard } from "./SuppressedCard";

interface Props {
  defects: Defect[];
  imageUrl: string;
  hoveredId: string | null;
  onHover: (id: string | null) => void;
  empty?: React.ReactNode;
  inspectionId: string | null;
  unclassified_anomalies?: UnclassifiedAnomaly[];
  suppressed_detections?: SuppressedDetection[];
}

export function DefectGallery({
  defects,
  imageUrl,
  hoveredId,
  onHover,
  empty,
  inspectionId,
  unclassified_anomalies,
  suppressed_detections,
}: Props) {
  const hasDefects = defects.length > 0;
  const hasAnomalies = (unclassified_anomalies?.length ?? 0) > 0;
  const hasSuppressed = (suppressed_detections?.length ?? 0) > 0;
  const isEmpty = !hasDefects && !hasAnomalies && !hasSuppressed;

  return (
    <ScrollArea className="h-full">
      <div className="p-4">
        {isEmpty ? (
          <div className="rounded-sm border border-dashed border-border p-8 text-center font-mono text-xs uppercase text-muted-foreground">
            {empty ?? "No defects match the current filters."}
          </div>
        ) : (
          <div className="space-y-6">
            {hasDefects && (
              <div>
                <h3 className="font-mono text-[10px] uppercase tracking-widest text-foreground mb-3">
                  Classified Defects ({defects.length})
                </h3>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {defects.map((d) => (
                    <DefectCard
                      key={d.id}
                      defect={d}
                      imageUrl={imageUrl}
                      isHovered={hoveredId === d.id}
                      onHover={onHover}
                      inspectionId={inspectionId}
                    />
                  ))}
                </div>
              </div>
            )}
            {hasAnomalies && (
              <div>
                <h3 className="font-mono text-[10px] uppercase tracking-widest text-amber-500 mb-3">
                  Rescued Anomalies (Stage 1) ({unclassified_anomalies!.length})
                </h3>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {unclassified_anomalies!.map((a) => (
                    <AnomalyCard key={a.id} anomaly={a} imageUrl={imageUrl} inspectionId={inspectionId} />
                  ))}
                </div>
              </div>
            )}
            {hasSuppressed && (
              <div>
                <h3 className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-3">
                  Suppressed Detections ({suppressed_detections!.length})
                </h3>
                <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                  {suppressed_detections!.map((s) => (
                    <SuppressedCard key={s.id} suppressed={s} imageUrl={imageUrl} inspectionId={inspectionId} />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </ScrollArea>
  );
}
