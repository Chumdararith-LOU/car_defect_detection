import { useCallback, useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LayoutGrid, Loader2, Shuffle } from "lucide-react";
import type { SplitStructure } from "@/lib/inspection/prepSchema";
import { fetchSplitStructure } from "@/lib/inspection/apiClient";
import { SplitStructurePanel } from "./SplitStructurePanel";
import { ResplitDialog } from "./ResplitDialog";
import { TileDialog } from "./TileDialog";

interface Props {
  datasetId: string;
  datasetName: string;
  totalImages: number;
  onPrepComplete: () => void;
}

export function DatasetPrepPanel({
  datasetId,
  datasetName,
  totalImages,
  onPrepComplete,
}: Props) {
  const [structure, setStructure] = useState<SplitStructure | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showResplit, setShowResplit] = useState(false);
  const [showTile, setShowTile] = useState(false);

  const loadStructure = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchSplitStructure(datasetId);
      setStructure(res);
    } catch (err: any) {
      setError(err.message || "Failed to detect split structure");
    } finally {
      setLoading(false);
    }
  }, [datasetId]);

  useEffect(() => {
    loadStructure();
  }, [loadStructure]);

  const handlePrepDone = () => {
    loadStructure();
    onPrepComplete();
  };

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Dataset Preparation</CardTitle>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowResplit(true)}
            >
              <Shuffle className="mr-1.5 h-4 w-4" /> Re-split
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowTile(true)}
            >
              <LayoutGrid className="mr-1.5 h-4 w-4" /> Tile
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" /> Detecting split
            structure...
          </div>
        )}
        {error && <p className="text-xs text-destructive">{error}</p>}
        {!loading && !error && structure && (
          <SplitStructurePanel structure={structure} />
        )}
      </CardContent>

      {showResplit && (
        <ResplitDialog
          datasetId={datasetId}
          totalImages={totalImages}
          onClose={() => setShowResplit(false)}
          onComplete={handlePrepDone}
        />
      )}
      {showTile && (
        <TileDialog
          datasetId={datasetId}
          sourceDatasetName={datasetName}
          onClose={() => setShowTile(false)}
          onComplete={handlePrepDone}
        />
      )}
    </Card>
  );
}
