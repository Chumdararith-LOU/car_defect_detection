import { useCallback, useEffect, useState } from "react";
import { Loader2, Plus, RefreshCw, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  listCheckpoints,
  scanCheckpoints,
  registerCheckpoint,
  deleteCheckpoint,
} from "@/lib/inspection/apiClient";
import type { Checkpoint, CheckpointOrigin } from "@/lib/inspection/platformSchema";

const ORIGIN_BADGE: Record<CheckpointOrigin, string> = {
  native_coco: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30",
  trained: "bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/30",
  surgery: "bg-purple-500/15 text-purple-700 dark:text-purple-400 border-purple-500/30",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export function CheckpointList() {
  const [checkpoints, setCheckpoints] = useState<Checkpoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [scanning, setScanning] = useState(false);
  const [registerOpen, setRegisterOpen] = useState(false);
  const [registerName, setRegisterName] = useState("");
  const [registerPath, setRegisterPath] = useState("");
  const [registerStage, setRegisterStage] = useState("stage2");
  const [registerNc, setRegisterNc] = useState("");
  const [registering, setRegistering] = useState(false);
  const [registerError, setRegisterError] = useState<string | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Checkpoint | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await listCheckpoints();
      setCheckpoints(res.checkpoints);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load checkpoints");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleScan = async () => {
    setScanning(true);
    try {
      const res = await scanCheckpoints();
      toast.success(`Scan complete: registered ${res.registered}, skipped ${res.skipped}`);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Scan failed");
    } finally {
      setScanning(false);
    }
  };

  const openRegister = () => {
    setRegisterName("");
    setRegisterPath("");
    setRegisterStage("stage2");
    setRegisterNc("");
    setRegisterError(null);
    setRegisterOpen(true);
  };

  const handleRegister = async () => {
    if (!registerName.trim() || !registerPath.trim()) {
      setRegisterError("Name and path are required.");
      return;
    }
    const nc = registerNc.trim() === "" ? undefined : Number(registerNc);
    if (nc !== undefined && (!Number.isFinite(nc) || nc < 0)) {
      setRegisterError("nc must be a non-negative number.");
      return;
    }
    setRegistering(true);
    setRegisterError(null);
    try {
      await registerCheckpoint({
        name: registerName.trim(),
        path: registerPath.trim(),
        stage: registerStage,
        nc,
      });
      toast.success(`Registered checkpoint "${registerName.trim()}"`);
      setRegisterOpen(false);
      await load();
    } catch (err) {
      setRegisterError(err instanceof Error ? err.message : "Register failed");
    } finally {
      setRegistering(false);
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteCheckpoint(deleteTarget.id);
      toast.success(`Deleted checkpoint "${deleteTarget.name}"`);
      setDeleteTarget(null);
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Delete failed");
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 text-muted-foreground">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading checkpoints...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div />
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleScan} disabled={scanning}>
            {scanning ? (
              <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
            ) : (
              <RefreshCw className="mr-1.5 h-4 w-4" />
            )}
            Scan
          </Button>
          <Button size="sm" onClick={openRegister}>
            <Plus className="mr-1.5 h-4 w-4" />
            Register
          </Button>
        </div>
      </div>

      {error && <p className="text-sm text-muted-foreground">{error}</p>}

      {checkpoints.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border p-8 text-center text-muted-foreground">
          No checkpoints registered. Scan the checkpoints directory or register one manually.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Name</th>
                <th className="px-4 py-3 text-left font-medium">Stage</th>
                <th className="px-4 py-3 text-left font-medium">Origin</th>
                <th className="px-4 py-3 text-right font-medium">NC</th>
                <th className="px-4 py-3 text-right font-medium">Size</th>
                <th className="px-4 py-3 text-left font-medium">Exists</th>
                <th className="px-4 py-3 text-left font-medium">Created</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border bg-card">
              {checkpoints.map((c) => (
                <tr key={c.id} className="transition-colors hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">{c.name}</td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">{c.stage || "—"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${ORIGIN_BADGE[c.origin] ?? ORIGIN_BADGE.trained}`}
                    >
                      {c.origin}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs">{c.nc}</td>
                  <td className="px-4 py-3 text-right font-mono text-xs">
                    {c.size_mb != null ? `${c.size_mb.toFixed(1)} MB` : "—"}
                  </td>
                  <td className="px-4 py-3">
                    {c.exists ? (
                      <span className="inline-flex items-center rounded-full border border-green-500/30 bg-green-500/15 px-2 py-0.5 text-xs font-medium text-green-700 dark:text-green-400">
                        ok
                      </span>
                    ) : (
                      <span className="inline-flex items-center rounded-full border border-red-500/30 bg-red-500/15 px-2 py-0.5 text-xs font-medium text-red-700 dark:text-red-400">
                        missing
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {formatDate(c.created_at)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeleteTarget(c)}
                        title="Delete"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </Button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      <Dialog open={registerOpen} onOpenChange={(open) => !open && setRegisterOpen(false)}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Register Checkpoint</DialogTitle>
          </DialogHeader>
          <div className="space-y-3">
            <div className="space-y-1.5">
              <Label htmlFor="cp-name">Name</Label>
              <Input
                id="cp-name"
                value={registerName}
                onChange={(e) => setRegisterName(e.target.value)}
                placeholder="e.g. yolo11n-sod"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="cp-path">Path</Label>
              <Input
                id="cp-path"
                value={registerPath}
                onChange={(e) => setRegisterPath(e.target.value)}
                placeholder="models/stage1/yolo11n.pt"
              />
            </div>
            <div className="space-y-1.5">
              <Label>Stage</Label>
              <Select value={registerStage} onValueChange={setRegisterStage}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="stage1">stage1</SelectItem>
                  <SelectItem value="stage2">stage2</SelectItem>
                  <SelectItem value="stage3">stage3</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="cp-nc">Number of classes (optional)</Label>
              <Input
                id="cp-nc"
                type="number"
                min={0}
                value={registerNc}
                onChange={(e) => setRegisterNc(e.target.value)}
                placeholder="e.g. 7"
              />
            </div>
            {registerError && <p className="text-sm text-destructive">{registerError}</p>}
          </div>
          <DialogFooter>
            <Button variant="ghost" onClick={() => setRegisterOpen(false)} disabled={registering}>
              Cancel
            </Button>
            <Button onClick={handleRegister} disabled={registering}>
              {registering ? (
                <>
                  <Loader2 className="mr-1.5 h-4 w-4 animate-spin" />
                  Registering...
                </>
              ) : (
                "Register"
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={!!deleteTarget}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete checkpoint</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete &quot;{deleteTarget?.name}&quot;? This removes the
              registry entry only — the file on disk is untouched.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel disabled={deleting}>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              disabled={deleting}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              {deleting ? "Deleting..." : "Delete"}
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
}
