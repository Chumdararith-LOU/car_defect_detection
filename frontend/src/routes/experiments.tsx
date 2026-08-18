import { createFileRoute } from "@tanstack/react-router";
import { ExperimentDashboard } from "@/components/Experiments";

export const Route = createFileRoute("/experiments")({
  component: ExperimentsPage,
});

function ExperimentsPage() {
  return <ExperimentDashboard />;
}
