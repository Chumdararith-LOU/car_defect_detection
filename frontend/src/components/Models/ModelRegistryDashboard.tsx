import { useCallback, useEffect, useState } from "react";
import type {
  ModelVersion,
  GateResult,
} from "@/lib/inspection/modelRegistrySchema";
import {
  fetchModelRegistryModels,
  evaluateModelGates,
  promoteModel,
  deployModel,
  rollbackModel,
} from "@/lib/inspection/apiClient";
import { ModelListTable } from "./ModelListTable";
import { ModelDetailPanel } from "./ModelDetailPanel";
import { PromoteDialog } from "./PromoteDialog";
import { DeployDialog } from "./DeployDialog";
import { RollbackDialog } from "./RollbackDialog";

export function ModelRegistryDashboard() {
  const [models, setModels] = useState<ModelVersion[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<ModelVersion | null>(null);
  const [promoteTarget, setPromoteTarget] = useState<ModelVersion | null>(null);
  const [deployTarget, setDeployTarget] = useState<ModelVersion | null>(null);
  const [rollbackTarget, setRollbackTarget] = useState<ModelVersion | null>(null);
  const [gateResults, setGateResults] = useState<GateResult[] | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionMessage, setActionMessage] = useState<string | null>(null);

  const loadModels = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetchModelRegistryModels();
      setModels(res.models);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load models");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const currentChampion = promoteTarget
    ? models.find(
        (m) => m.stage === promoteTarget.stage && m.status === "champion"
      ) ?? null
    : null;

  const handleOpenPromote = async (model: ModelVersion) => {
    setPromoteTarget(model);
    setGateResults(null);
    try {
      const res = await evaluateModelGates(model.id);
      setGateResults(res.gate_results);
    } catch {
      setGateResults([]);
    }
  };

  const handleConfirmPromote = async () => {
    if (!promoteTarget) return;
    setActionLoading(true);
    try {
      const res = await promoteModel(promoteTarget.id);
      setActionMessage(res.message);
      setPromoteTarget(null);
      await loadModels();
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : "Promotion failed");
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirmDeploy = async () => {
    if (!deployTarget) return;
    setActionLoading(true);
    try {
      const res = await deployModel(deployTarget.id);
      setActionMessage(res.message);
      setDeployTarget(null);
      await loadModels();
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : "Deployment failed");
    } finally {
      setActionLoading(false);
    }
  };

  const handleConfirmRollback = async () => {
    if (!rollbackTarget) return;
    setActionLoading(true);
    try {
      const res = await rollbackModel(rollbackTarget.stage);
      setActionMessage(res.message);
      setRollbackTarget(null);
      await loadModels();
    } catch (err) {
      setActionMessage(err instanceof Error ? err.message : "Rollback failed");
    } finally {
      setActionLoading(false);
    }
  };

  return (
    <div className="mx-auto max-w-7xl space-y-6 p-6">
      <div>
        <h1 className="text-2xl font-semibold">Model Registry</h1>
        <p className="text-sm text-muted-foreground">
          Manage model versions, promotion gates, and production deployment.
        </p>
      </div>

      {actionMessage && (
        <div className="flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 px-4 py-2 text-sm text-blue-800">
          <span>{actionMessage}</span>
          <button
            onClick={() => setActionMessage(null)}
            className="font-medium hover:text-blue-950"
          >
            ✕
          </button>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-2 text-sm text-red-800">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          Loading models...
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
          <div className="min-w-0 lg:col-span-2">
            <ModelListTable
              models={models}
              selectedId={selectedModel?.id ?? null}
              onSelect={setSelectedModel}
            />
          </div>
          <div className="min-w-0 rounded-lg border">
            <ModelDetailPanel
              model={selectedModel}
              onPromote={handleOpenPromote}
              onDeploy={setDeployTarget}
              onRollback={setRollbackTarget}
            />
          </div>
        </div>
      )}

      {promoteTarget && (
        <PromoteDialog
          candidate={promoteTarget}
          champion={currentChampion}
          gateResults={gateResults}
          isLoading={actionLoading}
          onConfirm={handleConfirmPromote}
          onClose={() => setPromoteTarget(null)}
        />
      )}

      {deployTarget && (
        <DeployDialog
          model={deployTarget}
          isLoading={actionLoading}
          onConfirm={handleConfirmDeploy}
          onClose={() => setDeployTarget(null)}
        />
      )}

      {rollbackTarget && (
        <RollbackDialog
          model={rollbackTarget}
          isLoading={actionLoading}
          onConfirm={handleConfirmRollback}
          onClose={() => setRollbackTarget(null)}
        />
      )}
    </div>
  );
}
