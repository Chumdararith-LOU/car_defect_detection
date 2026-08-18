import { createFileRoute } from "@tanstack/react-router";
import { PageHeader, PageShell } from "@/components/Layout";

export const Route = createFileRoute("/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  const apiBase = import.meta.env.VITE_API_BASE || "http://localhost:8010";

  return (
    <PageShell>
      <PageHeader title="Settings" subtitle="Runtime and connection configuration" />
      <div className="rounded-sm border border-border bg-card p-4 space-y-3">
        <div>
          <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
            Backend URL
          </p>
          <p className="font-mono text-xs text-foreground mt-1">{apiBase}</p>
        </div>
        <div className="border-t border-border pt-3">
          <p className="font-mono text-[10px] text-muted-foreground">
            Runtime configuration and training settings — Coming in Phase 7
          </p>
        </div>
      </div>
    </PageShell>
  );
}
