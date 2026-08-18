import { useEffect, useState } from "react";
import { Trash2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { deleteRecipe, listRecipes } from "@/lib/inspection/apiClient";
import type { Recipe } from "@/lib/inspection/platformSchema";
import { Badge } from "@/components/ui/badge";
import { ConfirmDialog, EmptyState } from "@/components/Shared";

export function RecipeList() {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    listRecipes()
      .then((res) => setRecipes(res.recipes))
      .catch(() => setRecipes([]))
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load();
  }, []);

  const [deleteId, setDeleteId] = useState<string | null>(null);

  function handleDelete(id: string, isPreset: boolean) {
    if (isPreset) {
      toast.error("Presets are immutable");
      return;
    }
    setDeleteId(id);
  }

  async function confirmDelete() {
    if (!deleteId) return;
    const id = deleteId;
    setDeleteId(null);
    try {
      await deleteRecipe(id);
      toast.success("Recipe deleted");
      load();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to delete recipe");
    }
  }

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading recipes...</p>;
  }

  if (recipes.length === 0) {
    return (
      <EmptyState title="No recipes yet" hint="Pick a preset above to create your first recipe." />
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-muted-foreground">
            <th className="px-3 py-2">Name</th>
            <th className="px-3 py-2">Stage</th>
            <th className="px-3 py-2">Freeze</th>
            <th className="px-3 py-2">LR</th>
            <th className="px-3 py-2">Loss</th>
            <th className="px-3 py-2">Epochs</th>
            <th className="px-3 py-2"></th>
          </tr>
        </thead>
        <tbody>
          {recipes.map((r) => (
            <tr key={r.id} className="border-b border-border hover:bg-muted/30">
              <td className="px-3 py-2">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{r.name}</span>
                  {r.is_preset && (
                    <Badge variant="secondary" className="text-[10px]">
                      preset
                    </Badge>
                  )}
                </div>
              </td>
              <td className="px-3 py-2 font-mono text-xs">{r.stage}</td>
              <td className="px-3 py-2 font-mono text-xs">{r.freeze_mode}</td>
              <td className="px-3 py-2 font-mono text-xs">{r.lr_mode}</td>
              <td className="px-3 py-2 font-mono text-xs">{r.loss_type}</td>
              <td className="px-3 py-2 font-mono text-xs">{r.epochs}</td>
              <td className="px-3 py-2 text-right">
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={r.is_preset}
                  onClick={() => handleDelete(r.id, r.is_preset)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <ConfirmDialog
        open={deleteId !== null}
        onOpenChange={(o) => {
          if (!o) setDeleteId(null);
        }}
        title="Delete recipe?"
        description="The recipe will be permanently removed. Presets cannot be deleted."
        confirmLabel="Delete Recipe"
        onConfirm={confirmDelete}
      />
    </div>
  );
}
