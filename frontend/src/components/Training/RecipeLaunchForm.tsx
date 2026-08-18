import { useEffect, useMemo, useState } from "react";
import { Loader2, Play } from "lucide-react";
import { Button } from "@/components/ui/button";
import { CheckpointPicker } from "@/components/Platform";
import { fetchDatasets, launchTrainingJob, listRecipes } from "@/lib/inspection/apiClient";
import type { DatasetSummary } from "@/lib/inspection/schema";
import type { Recipe } from "@/lib/inspection/platformSchema";
import type { LaunchTrainingRequest } from "@/lib/inspection/trainingSchema";

interface Props {
  onClose: () => void;
  onLaunched: () => void;
}

export function RecipeLaunchForm({ onClose, onLaunched }: Props) {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [datasets, setDatasets] = useState<DatasetSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [recipeId, setRecipeId] = useState("");
  const [datasetId, setDatasetId] = useState("");
  const [checkpointOverride, setCheckpointOverride] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([listRecipes(), fetchDatasets()])
      .then(([r, d]) => {
        setRecipes(r.recipes);
        setDatasets(d.datasets);
      })
      .catch(() => setError("Failed to load recipes or datasets"))
      .finally(() => setLoading(false));
  }, []);

  const recipe = recipes.find((r) => r.id === recipeId) ?? null;

  const stageDatasets = useMemo(
    () => (recipe ? datasets.filter((d) => d.stage === recipe.stage) : datasets),
    [datasets, recipe],
  );

  const isChainOnly = recipe?.base_strategy === "from_previous_step";
  const needsCheckpoint = recipe?.base_strategy === "from_checkpoint" && !recipe.base_checkpoint_id;
  const canLaunch =
    recipe != null &&
    datasetId !== "" &&
    !isChainOnly &&
    (!needsCheckpoint || checkpointOverride != null);

  const handleLaunch = async () => {
    if (!recipe) return;
    setSubmitting(true);
    setError(null);
    const request: LaunchTrainingRequest = {
      stage: recipe.stage,
      dataset_id: datasetId,
      recipe_id: recipe.id,
      base_checkpoint_id: checkpointOverride ?? undefined,
    };
    try {
      await launchTrainingJob(request);
      onLaunched();
      onClose();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to launch job");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <p className="text-xs text-muted-foreground">Loading recipes...</p>;
  }

  return (
    <div className="space-y-3">
      <div className="space-y-1.5">
        <label className="text-sm font-medium">Recipe</label>
        <select
          value={recipeId}
          onChange={(e) => {
            setRecipeId(e.target.value);
            setDatasetId("");
            setCheckpointOverride(null);
          }}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
        >
          <option value="">Select a recipe...</option>
          {recipes.map((r) => (
            <option key={r.id} value={r.id}>
              {r.name} ({r.stage})
            </option>
          ))}
        </select>
      </div>
      {recipe && (
        <p className="font-mono text-[10px] text-muted-foreground">
          freeze: {recipe.freeze_mode} · lr: {recipe.lr_mode} · loss: {recipe.loss_type} · epochs:{" "}
          {recipe.epochs} · imgsz: {recipe.imgsz}
        </p>
      )}
      {isChainOnly && (
        <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-400">
          This recipe uses base_strategy "from_previous_step" and can only run inside a chain.
        </div>
      )}
      <div className="space-y-1.5">
        <label className="text-sm font-medium">Dataset</label>
        <select
          value={datasetId}
          onChange={(e) => setDatasetId(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono"
        >
          <option value="">Select a dataset...</option>
          {stageDatasets.map((d) => (
            <option key={d.dataset_id} value={d.dataset_id}>
              {d.name} ({d.stage})
            </option>
          ))}
        </select>
      </div>
      <div className="space-y-1.5">
        <label className="text-xs font-medium text-muted-foreground">
          Base checkpoint override (optional)
        </label>
        <CheckpointPicker
          stage={recipe?.stage}
          value={checkpointOverride}
          onChange={setCheckpointOverride}
        />
        {needsCheckpoint && checkpointOverride == null && (
          <p className="text-[10px] text-amber-600 dark:text-amber-400">
            Recipe has no base checkpoint — select one to launch.
          </p>
        )}
      </div>
      {recipe && recipe.epochs > 5 && (
        <div className="rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-400">
          <strong>⚠️ Long Training Detected:</strong> {recipe.epochs} epochs may take several hours
          on Mac. The Mac safety guard clamps to 1 epoch unless overridden server-side.
        </div>
      )}
      {error && <p className="text-xs text-destructive">{error}</p>}
      <div className="flex justify-end gap-2 pt-2">
        <Button variant="ghost" onClick={onClose}>
          Cancel
        </Button>
        <Button onClick={handleLaunch} disabled={!canLaunch || submitting}>
          {submitting ? (
            <>
              <Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> Launching...
            </>
          ) : (
            <>
              <Play className="mr-1.5 h-4 w-4" /> Launch Recipe
            </>
          )}
        </Button>
      </div>
    </div>
  );
}
