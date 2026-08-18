import { createFileRoute } from "@tanstack/react-router";
import { TrainingDashboard } from "@/components/Training";

export const Route = createFileRoute("/training")({
  component: TrainingPage,
});

function TrainingPage() {
  return <TrainingDashboard />;
}
