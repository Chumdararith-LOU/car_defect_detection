import { createFileRoute } from "@tanstack/react-router";
import { ReviewDashboard } from "@/components/Review";

export const Route = createFileRoute("/review")({
  component: ReviewPage,
});

function ReviewPage() {
  return <ReviewDashboard />;
}
