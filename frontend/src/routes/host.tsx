import { createFileRoute } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { fetchHostProfile, type HostProfile } from "@/lib/inspection/apiClient";
import { PageHeader, PageShell } from "@/components/Layout";

export const Route = createFileRoute("/host")({
  component: HostPage,
});

function HostPage() {
  const [profile, setProfile] = useState<HostProfile | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchHostProfile()
      .then(setProfile)
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <PageShell>
        <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground">
          Loading host profile...
        </p>
      </PageShell>
    );
  }

  if (error) {
    return (
      <PageShell>
        <div className="rounded-sm border border-destructive/30 bg-destructive/10 p-4">
          <p className="font-mono text-[10px] uppercase tracking-widest text-destructive">
            Error: {error}
          </p>
        </div>
      </PageShell>
    );
  }

  if (!profile) return null;

  return (
    <PageShell>
      <PageHeader title="Host" subtitle="Hardware detection and runtime capabilities" />

      {/* Warnings */}
      {profile.warnings.length > 0 && (
        <div className="rounded-sm border border-yellow-500/30 bg-yellow-500/10 p-3">
          <p className="font-mono text-[10px] uppercase tracking-widest text-yellow-600 mb-1">
            Warnings
          </p>
          {profile.warnings.map((w, i) => (
            <p key={i} className="font-mono text-[10px] text-yellow-600">
              • {w}
            </p>
          ))}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {/* Machine Info */}
        <Card title="Machine">
          <Row label="Hostname" value={profile.machine.hostname} />
          <Row label="OS" value={profile.machine.os} />
          <Row label="Platform" value={profile.machine.platform} />
          <Row label="Arch" value={profile.machine.architecture} />
          <Row label="Python" value={profile.machine.python_version} />
        </Card>

        {/* CPU & Memory */}
        <Card title="Compute">
          <Row
            label="CPU Cores"
            value={`${profile.cpu.physical_cores}P / ${profile.cpu.logical_cores}L`}
          />
          <Row
            label="RAM"
            value={`${profile.memory.available_gb.toFixed(1)} / ${profile.memory.total_gb.toFixed(1)} GB free`}
          />
          <Row
            label="Disk"
            value={`${profile.disk.free_gb.toFixed(1)} / ${profile.disk.total_gb.toFixed(1)} GB free`}
          />
        </Card>

        {/* GPU */}
        <Card title="GPU">
          <Row label="CUDA" value={profile.gpu.cuda_available ? "Available" : "Not available"} />
          <Row label="MPS" value={profile.gpu.mps_available ? "Available" : "Not available"} />
          {profile.gpu.devices.map((dev) => (
            <div key={dev.index} className="mt-2 pt-2 border-t border-border">
              <Row label={`Device ${dev.index}`} value={dev.name} />
              {dev.total_vram_gb !== null && (
                <Row
                  label="VRAM"
                  value={`${(dev.free_vram_gb ?? 0).toFixed(1)} / ${dev.total_vram_gb.toFixed(1)} GB`}
                />
              )}
            </div>
          ))}
        </Card>

        {/* Model Availability */}
        <Card title="Model Availability">
          <ModelRow label="Stage 1 (SOD)" available={profile.models.stage1.available} />
          <ModelRow label="Stage 2 (Defect)" available={profile.models.stage2.available} />
          <ModelRow label="Stage 3 (Panel)" available={profile.models.stage3.available} />
          <ModelRow label="Stage 4 (Fusion)" available={profile.models.stage4.available} />
        </Card>

        {/* Capabilities */}
        <Card title="Capabilities">
          <BoolRow label="Infer Stage 1" value={profile.capabilities.can_infer_stage1} />
          <BoolRow label="Infer Stage 2" value={profile.capabilities.can_infer_stage2} />
          <BoolRow label="Infer Stage 3" value={profile.capabilities.can_infer_stage3} />
          <BoolRow label="Local GPU" value={profile.capabilities.can_use_local_gpu} />
        </Card>

        {/* Recommendations */}
        <Card title="Recommendations">
          <Row label="Runtime Mode" value={profile.recommendations.runtime_mode} />
          <Row label="Inference Device" value={profile.recommendations.inference_device} />
          <Row label="Training Device" value={profile.recommendations.training_device} />
        </Card>
      </div>
    </PageShell>
  );
}

/* ─── Helper Components ─── */

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="rounded-sm border border-border bg-card p-4">
      <p className="font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-3">
        {title}
      </p>
      <div className="space-y-1.5">{children}</div>
    </div>
  );
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center">
      <span className="font-mono text-[10px] text-muted-foreground">{label}</span>
      <span className="font-mono text-[10px] text-foreground">{value}</span>
    </div>
  );
}

function ModelRow({ label, available }: { label: string; available: boolean }) {
  return (
    <div className="flex justify-between items-center">
      <span className="font-mono text-[10px] text-muted-foreground">{label}</span>
      <span className={`font-mono text-[10px] ${available ? "text-green-500" : "text-red-500"}`}>
        {available ? "● Available" : "○ Missing"}
      </span>
    </div>
  );
}

function BoolRow({ label, value }: { label: string; value: boolean }) {
  return (
    <div className="flex justify-between items-center">
      <span className="font-mono text-[10px] text-muted-foreground">{label}</span>
      <span
        className={`font-mono text-[10px] ${value ? "text-green-500" : "text-muted-foreground"}`}
      >
        {value ? "Yes" : "No"}
      </span>
    </div>
  );
}
