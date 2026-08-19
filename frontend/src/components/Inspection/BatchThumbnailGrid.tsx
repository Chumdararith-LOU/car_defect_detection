import { cn } from "@/lib/utils";
import type { BatchState } from "@/hooks/useInspection";
import { ArrowLeft, Zap } from "lucide-react";
import { Button } from "@/components/ui/button";

interface Props {
  batch: BatchState;
  onBack: () => void;
  onSelect: (index: number) => void;
}

export function BatchThumbnailGrid({ batch, onBack, onSelect }: Props) {
  const avgMs = batch.totalMs / batch.items.length;
  const throughput = (batch.items.length / (batch.totalMs / 1000)).toFixed(1);

  return (
    <div className="p-4 border-b border-border">
      {/* Stats Header */}
      <div className="mb-3 flex items-center gap-3 font-mono text-[10px] text-muted-foreground">
        <Zap className="h-3 w-3 text-amber-400" />
        <span>Total: {(batch.totalMs / 1000).toFixed(1)}s</span>
        <span>·</span>
        <span>Avg: {avgMs.toFixed(0)}ms/image</span>
        <span>·</span>
        <span>{throughput} img/s</span>
        <span>·</span>
        <span>{batch.deviceUsed}</span>
      </div>

      {/* Thumbnail grid */}
      <div className="grid grid-cols-4 gap-2">
        {batch.items.map((item, idx) => (
          <button
            key={idx}
            onClick={() => onSelect(idx)}
            className={cn(
              "relative aspect-[4/3] rounded-sm border-2 overflow-hidden transition-all hover:border-primary",
              "border-border",
            )}
          >
            <img src={item.thumbnail} alt={item.filename} className="h-full w-full object-cover" />
            <div className="absolute bottom-0 left-0 right-0 bg-black/70 text-white text-[9px] font-mono px-1 py-0.5 truncate">
              {item.payload.total_defects_found} defects
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
