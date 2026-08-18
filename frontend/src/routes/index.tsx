import { useCallback, useEffect, useState } from "react";
import { createFileRoute } from "@tanstack/react-router";
import demoVehicle from "@/assets/demo-vehicle.jpg";
import { useInspection } from "@/hooks/useInspection";
import { ControlSidebar } from "@/components/Inspection/ControlSidebar";
import { InspectionCanvas } from "@/components/Inspection/InspectionCanvas";
import { DefectGallery } from "@/components/Inspection/gallery";
import { SummaryCard } from "@/components/Inspection/SummaryCard";
import { Activity } from "lucide-react";

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "AI Exterior Defect Inspection Dashboard" },
      {
        name: "description",
        content:
          "Multi-stage AI pipeline for component-aware automotive exterior defect detection and industrial quality inspection.",
      },
      {
        property: "og:title",
        content: "AI Exterior Defect Inspection Dashboard",
      },
      {
        property: "og:description",
        content:
          "Pre-screen, tiled detection, and component context mapping for automotive quality inspection.",
      },
    ],
  }),
  component: InspectionDashboard,
});

function InspectionDashboard() {
  const {
    state,
    filteredDefects,
    setImage,
    run,
    reset,
    setFilters,
    setViewStage,
    setStageToggles,
  } = useInspection({ imageUrl: demoVehicle, imageName: "demo-vehicle.jpg" });
  const [hoveredId, setHoveredId] = useState<string | null>(null);

  const onImage = useCallback(
    (file: File) => {
      const url = URL.createObjectURL(file);
      setImage(url, file.name, file);
    },
    [setImage],
  );

  // Force dark theme for the industrial dashboard look.
  useEffect(() => {
    const html = document.documentElement;
    html.classList.add("dark");
    return () => html.classList.remove("dark");
  }, []);

  return (
    <div className="flex h-screen w-full flex-col bg-background text-foreground">
      <header className="flex items-center justify-between border-b border-border px-5 py-2.5">
        <div className="flex items-center gap-3">
          <div className="grid h-8 w-8 place-items-center rounded-sm bg-primary text-primary-foreground">
            <Activity className="h-4 w-4" />
          </div>
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
              AI Farm Robotics · Line Inspection
            </p>
            <h1 className="text-sm font-semibold">Component-Aware Exterior Defect Pipeline</h1>
          </div>
        </div>
        <div className="hidden items-center gap-4 sm:flex">
          <div className="flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground">
            <span className="text-primary">S1</span> PRE-SCREEN
            <span className="text-border">›</span>
            <span className="text-primary">S2</span> TILE-SEG
            <span className="text-border">›</span>
            <span className="text-primary">S3</span> CONTEXT
          </div>
          <div className="h-4 w-px bg-border" />
          <span className="font-mono text-[10px] text-muted-foreground">v2.0</span>
        </div>
      </header>

      <div className="grid flex-1 grid-cols-1 overflow-hidden xl:grid-cols-[300px_minmax(0,1fr)_400px]">
        <ControlSidebar
          imageName={state.imageName}
          stage={state.stage}
          message={state.message}
          payload={state.payload}
          filters={state.filters}
          viewStage={state.viewStage}
          onImage={onImage}
          onRun={run}
          onReset={reset}
          onFilters={setFilters}
          onViewStage={setViewStage}
          enableStage1={state.enableStage1}
          enableStage2={state.enableStage2}
          enableStage3={state.enableStage3}
          onStageToggles={setStageToggles}
        />

        <main className="flex min-h-[500px] flex-col overflow-hidden border-border xl:border-x">
          {state.imageUrl && (
            <InspectionCanvas
              imageUrl={state.imageUrl}
              payload={state.payload}
              visibleDefects={filteredDefects}
              hoveredId={hoveredId}
              onHover={setHoveredId}
              viewStage={state.viewStage}
            />
          )}
        </main>

        <section className="flex min-h-[400px] flex-col overflow-hidden bg-sidebar/40">
          <div className="border-b border-border p-4">
            <p className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
              Zone C · Diagnostics
            </p>
            <h2 className="mt-0.5 text-sm font-semibold uppercase tracking-wide">
              Defect gallery & report
            </h2>
          </div>
          <div className="p-4 pb-0">
            <SummaryCard
              payload={state.payload}
              filteredCount={filteredDefects.length}
              disabledStages={
                state.payload?.disabled_stages ?? [
                  ...(state.enableStage1 ? [] : ["stage1"]),
                  ...(state.enableStage2 ? [] : ["stage2"]),
                  ...(state.enableStage3 ? [] : ["stage3"]),
                ]
              }
            />
          </div>
          <div className="min-h-0 flex-1">
            <DefectGallery
              defects={filteredDefects}
              imageUrl={state.imageUrl ?? demoVehicle}
              inspectionId={state.payload?.inspection_id ?? null}
              hoveredId={hoveredId}
              unclassified_anomalies={state.payload?.unclassified_anomalies}
              suppressed_detections={state.payload?.suppressed_detections}
              onHover={setHoveredId}
              empty={
                state.payload?.inspection_status === "PASS"
                  ? "Pre-screen returned PASS. No heavy processing triggered."
                  : state.payload
                    ? "No defects match the current filters."
                    : "Run an inspection to populate the gallery."
              }
            />
          </div>
        </section>
      </div>
    </div>
  );
}
