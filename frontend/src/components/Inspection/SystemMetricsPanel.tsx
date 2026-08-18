import { useEffect, useState } from "react";
import { fetchSystemMetrics, type SystemMetrics } from "@/lib/inspection/apiClient";
import { Cpu, HardDrive, Zap } from "lucide-react";

export function SystemMetricsPanel() {
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);

  useEffect(() => {
    let active = true;
    const poll = async () => {
      try {
        const data = await fetchSystemMetrics();
        if (active) setMetrics(data);
      } catch (e) {
        // ignore polling errors
      }
    };
    poll();
    const id = setInterval(poll, 2000); // Poll every 2 seconds
    return () => { active = false; clearInterval(id); };
  }, []);

  if (!metrics) return null;

  const ramPercent =
    metrics.ram_total_gb > 0
      ? Math.min(100, (metrics.ram_used_gb / metrics.ram_total_gb) * 100)
      : 0;
  const gpuMemPercent =
    metrics.gpu_name !== null && metrics.gpu_vram_total_gb
      ? Math.min(
          100,
          ((metrics.gpu_vram_used_gb ?? 0) / metrics.gpu_vram_total_gb) * 100,
        )
      : 0;

  return (
    <div className="space-y-2 rounded-sm border border-border bg-card/40 p-3">
      <p className="font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
        System Telemetry
      </p>

      {/* CPU */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-[10px]">
          <span className="flex items-center gap-1 font-mono uppercase text-muted-foreground">
            <Cpu className="h-3 w-3" /> CPU
          </span>
          <span className="font-mono">{metrics.cpu_percent.toFixed(0)}%</span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div className="h-full bg-primary transition-all" style={{ width: `${metrics.cpu_percent}%` }} />
        </div>
      </div>

      {/* RAM */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-[10px]">
          <span className="flex items-center gap-1 font-mono uppercase text-muted-foreground">
            <HardDrive className="h-3 w-3" /> RAM
          </span>
          <span className="font-mono">{metrics.ram_used_gb} / {metrics.ram_total_gb} GB</span>
        </div>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
          <div className="h-full bg-primary transition-all" style={{ width: `${ramPercent}%` }} />
        </div>
      </div>

      {/* GPU */}
      {metrics.gpu_name !== null ? (
        <div className="space-y-1">
          <div className="flex items-center justify-between text-[10px]">
            <span
              className="flex min-w-0 items-center gap-1 font-mono uppercase text-muted-foreground"
              title={metrics.gpu_name}
            >
              <Zap className="h-3 w-3 shrink-0" />
              <span className="truncate">{metrics.gpu_name}</span>
            </span>
            <span className="shrink-0 font-mono">
              {metrics.gpu_vram_used_gb ?? 0} / {metrics.gpu_vram_total_gb ?? 0} GB
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
            <div
              className="h-full bg-primary transition-all"
              style={{ width: `${gpuMemPercent}%` }}
            />
          </div>
          {metrics.gpu_utilization_percent !== null && (
            <p className="text-right font-mono text-[10px] text-muted-foreground">
              {metrics.gpu_utilization_percent.toFixed(0)}% UTIL
            </p>
          )}
        </div>
      ) : (
        <div className="flex items-center gap-1 font-mono text-[10px] uppercase text-muted-foreground/60">
          <Zap className="h-3 w-3" /> No GPU detected
        </div>
      )}
    </div>
  );
}
