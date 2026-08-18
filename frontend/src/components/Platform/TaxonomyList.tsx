import { useCallback, useEffect, useState } from "react";
import { Loader2, Plus, Pencil, Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
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
import { listTaxonomies, deleteTaxonomy } from "@/lib/inspection/apiClient";
import type { Taxonomy, PlatformStage } from "@/lib/inspection/platformSchema";
import { TaxonomyEditor } from "./TaxonomyEditor";

const STAGE_BADGE: Record<PlatformStage, string> = {
  stage1: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30",
  stage2: "bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/30",
  stage3: "bg-purple-500/15 text-purple-700 dark:text-purple-400 border-purple-500/30",
};

function formatDate(iso: string): string {
  return new Date(iso).toLocaleString();
}

export function TaxonomyList() {
  const [taxonomies, setTaxonomies] = useState<Taxonomy[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editorOpen, setEditorOpen] = useState(false);
  const [editingTaxonomy, setEditingTaxonomy] = useState<Taxonomy | null>(null);
  const [deleteTarget, setDeleteTarget] = useState<Taxonomy | null>(null);
  const [deleting, setDeleting] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await listTaxonomies();
      setTaxonomies(res.taxonomies);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load taxonomies");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setDeleting(true);
    try {
      await deleteTaxonomy(deleteTarget.id);
      setDeleteTarget(null);
      await load();
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Delete failed";
      if (msg.includes("409") || msg.includes("conflict")) {
        setError(msg);
      } else {
        setError(msg);
      }
      setDeleteTarget(null);
    } finally {
      setDeleting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8 text-muted-foreground">
        <Loader2 className="mr-2 h-4 w-4 animate-spin" /> Loading taxonomies...
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div />
        <Button
          size="sm"
          onClick={() => {
            setEditingTaxonomy(null);
            setEditorOpen(true);
          }}
        >
          <Plus className="mr-1.5 h-4 w-4" />
          New taxonomy
        </Button>
      </div>

      {error && <p className="text-sm text-muted-foreground">{error}</p>}

      {taxonomies.length === 0 ? (
        <div className="rounded-lg border border-dashed border-border p-8 text-center text-muted-foreground">
          No taxonomies found. Create one to get started.
        </div>
      ) : (
        <div className="overflow-x-auto rounded-lg border border-border">
          <table className="w-full text-sm">
            <thead className="bg-muted/50 text-xs uppercase tracking-wider text-muted-foreground">
              <tr>
                <th className="px-4 py-3 text-left font-medium">Name</th>
                <th className="px-4 py-3 text-left font-medium">Stage</th>
                <th className="px-4 py-3 text-right font-medium">Classes</th>
                <th className="px-4 py-3 text-left font-medium">Updated</th>
                <th className="px-4 py-3 text-right font-medium">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-border bg-card">
              {taxonomies.map((t) => (
                <tr key={t.id} className="transition-colors hover:bg-muted/30">
                  <td className="px-4 py-3 font-medium">{t.name}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center rounded-full border px-2 py-0.5 text-xs font-medium ${STAGE_BADGE[t.stage]}`}
                    >
                      {t.stage}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right font-mono text-xs">{t.class_names.length}</td>
                  <td className="px-4 py-3 text-xs text-muted-foreground">
                    {formatDate(t.updated_at)}
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex justify-end gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          setEditingTaxonomy(t);
                          setEditorOpen(true);
                        }}
                        title="Edit"
                      >
                        <Pencil className="h-3.5 w-3.5" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setDeleteTarget(t)}
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

      <TaxonomyEditor
        open={editorOpen}
        taxonomy={editingTaxonomy}
        onClose={() => setEditorOpen(false)}
        onSaved={load}
      />

      <AlertDialog
        open={!!deleteTarget}
        onOpenChange={(open) => {
          if (!open) setDeleteTarget(null);
        }}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete taxonomy</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete "{deleteTarget?.name}"? This cannot be undone.
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
