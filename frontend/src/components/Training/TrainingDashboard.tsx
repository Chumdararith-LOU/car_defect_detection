import { useEffect, useState } from "react";
import type { TrainingJob } from "@/lib/inspection/trainingSchema";
import { fetchTrainingJobs, stopTrainingJob } from "@/lib/inspection/apiClient";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/Shared";
import { Play, Plus } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { PageHeader, PageShell } from "@/components/Layout";
import { JobListTable } from "./JobListTable";
import { JobDetailPanel } from "./JobDetailPanel";
import { LaunchTrainingDialog } from "./LaunchTrainingDialog";
import { StrategyPresetPicker } from "./StrategyPresetPicker";
import { RecipeBuilder } from "./RecipeBuilder";
import { RecipeList } from "./RecipeList";
import { ChainList } from "@/components/Chains";
import type { Recipe } from "@/lib/inspection/platformSchema";

export function TrainingDashboard() {
  const [jobs, setJobs] = useState<TrainingJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedJobId, setSelectedJobId] = useState<string | null>(null);
  const [showLaunchDialog, setShowLaunchDialog] = useState(false);
  const [showRecipeBuilder, setShowRecipeBuilder] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState<Recipe | undefined>(undefined);
  const [recipesRefreshKey, setRecipesRefreshKey] = useState(0);

  const loadJobs = async () => {
    try {
      setLoading(true);
      const res = await fetchTrainingJobs();
      setJobs(res.jobs);
    } catch (err) {
      console.error("Failed to load jobs", err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs();
    const interval = setInterval(loadJobs, 5000);
    return () => clearInterval(interval);
  }, []);

  const [stopJobId, setStopJobId] = useState<string | null>(null);

  const handleStopJob = (jobId: string) => setStopJobId(jobId);

  const confirmStopJob = async () => {
    if (!stopJobId) return;
    const id = stopJobId;
    setStopJobId(null);
    try {
      await stopTrainingJob(id);
      toast.success("Job stop requested");
      loadJobs();
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to stop job");
    }
  };

  const handlePresetSelect = (preset: Recipe) => {
    setSelectedPreset(preset);
    setShowRecipeBuilder(true);
  };

  const handleRecipeSaved = () => {
    setSelectedPreset(undefined);
    setRecipesRefreshKey((k) => k + 1);
  };

  if (selectedJobId) {
    return (
      <PageShell>
        <JobDetailPanel jobId={selectedJobId} onBack={() => setSelectedJobId(null)} />
      </PageShell>
    );
  }

  return (
    <PageShell>
      <PageHeader
        title="Training & Experiments"
        subtitle="Launch training jobs, manage recipes, and monitor progress."
      />
      <Tabs defaultValue="jobs">
        <TabsList>
          <TabsTrigger value="jobs">Jobs</TabsTrigger>
          <TabsTrigger value="recipes">Recipes</TabsTrigger>
          <TabsTrigger value="chains">Chains</TabsTrigger>
        </TabsList>
        <TabsContent value="jobs">
          <div className="flex items-center justify-end">
            <Button size="sm" onClick={() => setShowLaunchDialog(true)}>
              <Play className="h-4 w-4 mr-1.5" />
              Launch Training
            </Button>
          </div>
          <JobListTable
            jobs={jobs}
            loading={loading}
            onSelectJob={(job) => setSelectedJobId(job.id)}
            onStopJob={handleStopJob}
          />
          {showLaunchDialog && (
            <LaunchTrainingDialog
              onClose={() => setShowLaunchDialog(false)}
              onLaunched={loadJobs}
            />
          )}
          <ConfirmDialog
            open={stopJobId !== null}
            onOpenChange={(o) => {
              if (!o) setStopJobId(null);
            }}
            title="Stop training job?"
            description="The training process will be terminated and the job marked as cancelled."
            confirmLabel="Stop Job"
            onConfirm={confirmStopJob}
          />
        </TabsContent>
        <TabsContent value="recipes" className="space-y-6">
          <div className="flex items-center justify-end">
            <Button size="sm" onClick={() => setShowRecipeBuilder(true)}>
              <Plus className="h-4 w-4 mr-1.5" />
              New Recipe
            </Button>
          </div>
          <StrategyPresetPicker onSelect={handlePresetSelect} />
          <RecipeList key={recipesRefreshKey} />
          <RecipeBuilder
            open={showRecipeBuilder}
            onOpenChange={setShowRecipeBuilder}
            preset={selectedPreset}
            onSaved={handleRecipeSaved}
          />
        </TabsContent>
        <TabsContent value="chains" className="space-y-6">
          <ChainList />
        </TabsContent>
      </Tabs>
    </PageShell>
  );
}
