import { useEffect, useState } from "react";
import { Play, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { listChains, startChainRun } from "@/lib/inspection/apiClient";
import type { Chain } from "@/lib/inspection/platformSchema";
import { ChainRunStatus } from "./ChainRunStatus";
import { EmptyState } from "@/components/Shared";

export function ChainList() {
  const [chains, setChains] = useState<Chain[]>([]);
  const [loading, setLoading] = useState(true);
  const [runningChainId, setRunningChainId] = useState<string | null>(null);
  const [activeRunId, setActiveRunId] = useState<string | null>(null);

  useEffect(() => {
    listChains()
      .then((res) => setChains(res.chains))
      .catch(() => setChains([]))
      .finally(() => setLoading(false));
  }, []);

  const handleRun = async (chainId: string) => {
    setRunningChainId(chainId);
    try {
      const res = await startChainRun(chainId);
      setActiveRunId(res.run_id);
      toast.success("Chain run started");
    } catch (e) {
      toast.error(e instanceof Error ? e.message : "Failed to start chain");
    } finally {
      setRunningChainId(null);
    }
  };

  if (loading) {
    return <p className="text-sm text-muted-foreground">Loading chains...</p>;
  }

  if (chains.length === 0) {
    return <EmptyState title="No chains defined yet" />;
  }

  return (
    <div className="space-y-6">
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-border text-left text-xs text-muted-foreground">
              <th className="px-3 py-2">Name</th>
              <th className="px-3 py-2">Stage</th>
              <th className="px-3 py-2">Steps</th>
              <th className="px-3 py-2">Created</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {chains.map((c) => (
              <tr key={c.id} className="border-b border-border hover:bg-muted/30">
                <td className="px-3 py-2 font-medium">{c.name}</td>
                <td className="px-3 py-2 font-mono text-xs">{c.stage}</td>
                <td className="px-3 py-2 font-mono text-xs">{c.steps.length}</td>
                <td className="px-3 py-2 text-xs text-muted-foreground">
                  {new Date(c.created_at).toLocaleDateString()}
                </td>
                <td className="px-3 py-2 text-right">
                  <Button
                    size="sm"
                    variant="outline"
                    disabled={runningChainId === c.id}
                    onClick={() => handleRun(c.id)}
                  >
                    {runningChainId === c.id ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Play className="h-4 w-4" />
                    )}
                    Run
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {activeRunId && <ChainRunStatus runId={activeRunId} />}
    </div>
  );
}
