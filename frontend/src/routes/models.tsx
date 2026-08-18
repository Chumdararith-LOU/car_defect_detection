import { useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import { Scissors } from "lucide-react";
import { ModelRegistryDashboard } from "@/components/Models";
import { ModelTracksView } from "@/components/Models/ModelTracksView";
import { TaxonomyList, CheckpointList } from "@/components/Platform";
import { HeadSurgeryDialog } from "@/components/Surgery";
import { PageHeader, PageShell } from "@/components/Layout";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export const Route = createFileRoute("/models")({
  component: ModelsPage,
});

function ModelsPage() {
  const [showSurgery, setShowSurgery] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);
  return (
    <Tabs defaultValue="registry">
      <PageShell className="space-y-4">
        <TabsList>
          <TabsTrigger value="registry">Registry</TabsTrigger>
          <TabsTrigger value="tracks">Tracks</TabsTrigger>
          <TabsTrigger value="taxonomies">Taxonomies</TabsTrigger>
          <TabsTrigger value="checkpoints">Checkpoints</TabsTrigger>
        </TabsList>
      </PageShell>
      <TabsContent value="registry">
        <ModelRegistryDashboard />
      </TabsContent>
      <TabsContent value="tracks">
        <PageShell>
          <PageHeader
            title="Model Tracks"
            subtitle="Lifecycle view of candidates, champions, and deployed models per pipeline stage."
          />
          <ModelTracksView />
        </PageShell>
      </TabsContent>
      <TabsContent value="taxonomies">
        <PageShell>
          <PageHeader title="Taxonomies" subtitle="Define class taxonomies per pipeline stage." />
          <TaxonomyList />
        </PageShell>
      </TabsContent>
      <TabsContent value="checkpoints">
        <PageShell>
          <PageHeader
            title="Checkpoints"
            subtitle="Registered model weights available to pipeline stages."
            actions={
              <Button size="sm" onClick={() => setShowSurgery(true)}>
                <Scissors className="h-4 w-4" />
                Head Surgery
              </Button>
            }
          />
          <CheckpointList key={refreshKey} />
          <HeadSurgeryDialog
            open={showSurgery}
            onOpenChange={setShowSurgery}
            onCompleted={() => setRefreshKey((k) => k + 1)}
          />
        </PageShell>
      </TabsContent>
    </Tabs>
  );
}
