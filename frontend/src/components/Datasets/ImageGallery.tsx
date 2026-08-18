import { useEffect, useState } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { fetchDatasetImages, getDatasetImageUrl } from "@/lib/inspection/apiClient";
import { ImageViewer } from "./ImageViewer";

interface Props {
  datasetId: string;
}

export function ImageGallery({ datasetId }: Props) {
  const [images, setImages] = useState<string[]>([]);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [totalImages, setTotalImages] = useState(0);
  const [loading, setLoading] = useState(true);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const res = await fetchDatasetImages(datasetId, page, 20);
        setImages(res.images);
        setTotalPages(res.total_pages);
        setTotalImages(res.total);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [datasetId, page]);

  if (loading && images.length === 0) {
    return <div className="p-8 text-center text-muted-foreground">Loading images...</div>;
  }

  if (totalImages === 0) {
    return (
      <div className="p-8 text-center text-muted-foreground border border-border rounded-lg bg-card">
        No images found in this dataset split.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        {images.map((filename) => (
          <button
            key={filename}
            onClick={() => setSelectedImage(filename)}
            className="group relative aspect-square overflow-hidden rounded-md border border-border bg-muted/30 hover:border-primary transition-colors"
          >
            <img
              src={getDatasetImageUrl(datasetId, filename)}
              alt={filename}
              className="h-full w-full object-cover transition-transform group-hover:scale-105"
              loading="lazy"
            />
            <div className="absolute inset-x-0 bottom-0 bg-black/60 p-1.5 opacity-0 group-hover:opacity-100 transition-opacity">
              <p className="text-[10px] text-white font-mono truncate">{filename}</p>
            </div>
          </button>
        ))}
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <p className="text-muted-foreground">
            Showing {(page - 1) * 20 + 1}–{Math.min(page * 20, totalImages)} of {totalImages}
          </p>
          <div className="flex items-center gap-2">
            <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              <ChevronLeft className="h-4 w-4" /> Prev
            </Button>
            <span className="font-mono text-xs">Page {page} of {totalPages}</span>
            <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              Next <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      )}

      {/* Viewer Modal */}
      {selectedImage && (
        <ImageViewer
          datasetId={datasetId}
          filename={selectedImage}
          onClose={() => setSelectedImage(null)}
        />
      )}
    </div>
  );
}
