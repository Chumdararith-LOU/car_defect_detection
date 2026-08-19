import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Loader2, Pencil, Check, X } from "lucide-react";
import { toast } from "sonner";
import { fetchBatches, renameBatch, type BatchSummary } from "@/lib/inspection/apiClient";

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onOpenBatch: (batch: BatchSummary) => void;
}

export function PastBatchesDialog({ open, onOpenChange, onOpenBatch }: Props) {
  const [batches, setBatches] = useState<BatchSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editName, setEditName] = useState("");

  useEffect(() => {
    if (open) {
      setLoading(true);
      fetchBatches()
        .then((res) => setBatches(res.batches))
        .catch(() => toast.error("Failed to load batches"))
        .finally(() => setLoading(false));
    }
  }, [open]);

  const handleSaveRename = async (batchId: string) => {
    if (!editName.trim()) return;
    try {
      const updated = await renameBatch(batchId, editName.trim());
      setBatches((prev) => prev.map((b) => (b.batch_id === batchId ? updated : b)));
      setEditingId(null);
      toast.success("Batch renamed");
    } catch {
      toast.error("Failed to rename batch");
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Past Batches</DialogTitle>
        </DialogHeader>
        <div className="flex-1 overflow-y-auto border rounded-md divide-y">
          {loading && <p className="p-4 text-center text-muted-foreground">Loading...</p>}
          {!loading && batches.length === 0 && (
            <p className="p-4 text-center text-muted-foreground">No past batches found. Run an inspection first.</p>
          )}
          {batches.map((batch) => (
            <div key={batch.batch_id} className="p-3 flex items-center gap-3">
              <div className="flex-1 min-w-0">
                {editingId === batch.batch_id ? (
                  <div className="flex items-center gap-2">
                    <Input
                      value={editName}
                      onChange={(e) => setEditName(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleSaveRename(batch.batch_id)}
                      className="h-7 text-sm"
                      autoFocus
                    />
                    <Button size="icon" variant="ghost" className="h-7 w-7" onClick={() => handleSaveRename(batch.batch_id)}>
                      <Check className="h-3 w-3" />
                    </Button>
                    <Button size="icon" variant="ghost" className="h-7 w-7" onClick={() => setEditingId(null)}>
                      <X className="h-3 w-3" />
                    </Button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-sm truncate">{batch.name}</p>
                    <Button
                      size="icon"
                      variant="ghost"
                      className="h-6 w-6 text-muted-foreground hover:text-foreground"
                      onClick={() => {
                        setEditingId(batch.batch_id);
                        setEditName(batch.name);
                      }}
                    >
                      <Pencil className="h-3 w-3" />
                    </Button>
                  </div>
                )}
                <p className="text-xs text-muted-foreground mt-0.5">
                  {new Date(batch.created_at).toLocaleString()} · {batch.count} images ·{" "}
                  {batch.fail_count} FAIL / {batch.pass_count} PASS · {batch.total_defects} defects
                </p>
              </div>
              <Button size="sm" variant="outline" onClick={() => onOpenBatch(batch)}>
                Open
              </Button>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
