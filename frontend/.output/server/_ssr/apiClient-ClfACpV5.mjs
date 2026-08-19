//#region node_modules/.nitro/vite/services/ssr/assets/apiClient-ClfACpV5.js
var API_BASE = "http://localhost:8010";
async function runInspection(params) {
	const formData = new FormData();
	formData.append("file", params.file);
	if (params.modelName) formData.append("model_name", params.modelName);
	if (params.stage2ModelName) formData.append("stage2_model_name", params.stage2ModelName);
	if (params.stage2Mode) formData.append("stage2_mode", params.stage2Mode);
	if (params.stage2Preset) formData.append("stage2_preset", params.stage2Preset);
	if (params.stage2Conf !== void 0) formData.append("stage2_conf", String(params.stage2Conf));
	if (params.device) formData.append("device", params.device);
	formData.append("enable_stage1", String(params.enableStage1 ?? true));
	formData.append("enable_stage2", String(params.enableStage2 ?? true));
	formData.append("enable_stage3", String(params.enableStage3 ?? true));
	const res = await fetch(`${API_BASE}/api/inspect`, {
		method: "POST",
		body: formData
	});
	if (!res.ok) throw new Error(`API Error: ${res.statusText}`);
	return res.json();
}
async function fetchSystemDevices() {
	const res = await fetch(`${API_BASE}/api/system/devices`);
	if (!res.ok) throw new Error("Failed to fetch devices");
	return res.json();
}
async function fetchSystemMetrics() {
	const res = await fetch(`${API_BASE}/api/system/metrics`);
	if (!res.ok) throw new Error("Failed to fetch metrics");
	return res.json();
}
async function fetchHostProfile() {
	const res = await fetch(`${API_BASE}/api/host/profile`);
	if (!res.ok) throw new Error(`Failed to fetch host profile: ${res.statusText}`);
	return res.json();
}
async function fetchReviewQueue() {
	const res = await fetch(`${API_BASE}/api/review-queue`);
	if (!res.ok) throw new Error(`Failed to fetch review queue: ${res.statusText}`);
	return res.json();
}
async function submitReview(payload) {
	const res = await fetch(`${API_BASE}/api/reviews`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload)
	});
	if (!res.ok) throw new Error(`Failed to submit review: ${res.statusText}`);
	return res.json();
}
async function updateReview(reviewId, payload) {
	const res = await fetch(`${API_BASE}/api/reviews/${reviewId}`, {
		method: "PATCH",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(payload)
	});
	if (!res.ok) throw new Error(`Failed to update review: ${res.statusText}`);
	return res.json();
}
async function deleteReview(reviewId) {
	const res = await fetch(`${API_BASE}/api/reviews/${reviewId}`, { method: "DELETE" });
	if (!res.ok) throw new Error(`Failed to delete review: ${res.statusText}`);
}
async function fetchDatasets() {
	const res = await fetch(`${API_BASE}/api/datasets`);
	if (!res.ok) throw new Error(`Failed to fetch datasets: ${res.statusText}`);
	return res.json();
}
async function fetchDatasetDetail(datasetId) {
	const res = await fetch(`${API_BASE}/api/datasets/${datasetId}`);
	if (!res.ok) throw new Error(`Failed to fetch dataset detail: ${res.statusText}`);
	return res.json();
}
async function runLeakageAudit(datasetId) {
	const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/audit`, { method: "POST" });
	if (!res.ok) throw new Error(`Failed to run leakage audit: ${res.statusText}`);
	return res.json();
}
async function fetchAllReviews() {
	const res = await fetch(`${API_BASE}/api/reviews`);
	if (!res.ok) throw new Error(`Failed to fetch reviews: ${res.statusText}`);
	return res.json();
}
async function buildDataset(request) {
	const res = await fetch(`${API_BASE}/api/datasets/build`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(request)
	});
	if (!res.ok) throw new Error(`Failed to build dataset: ${res.statusText}`);
	return res.json();
}
function getDatasetImageUrl(datasetId, filename, split = "train") {
	return `${API_BASE}/api/datasets/${datasetId}/images/${encodeURIComponent(filename)}?split=${split}`;
}
async function fetchDatasetImages(datasetId, page = 1, size = 20, split = "train") {
	const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/images?page=${page}&size=${size}&split=${split}`);
	if (!res.ok) throw new Error(`Failed to fetch dataset images: ${res.statusText}`);
	return res.json();
}
async function fetchDatasetImageLabels(datasetId, filename, split = "train") {
	const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/images/${encodeURIComponent(filename)}/labels?split=${split}`);
	if (!res.ok) throw new Error(`Failed to fetch image labels: ${res.statusText}`);
	return res.json();
}
async function reclassifyAnnotation(datasetId, filename, annotationIndex, newClassId, split = "train") {
	const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/images/${encodeURIComponent(filename)}/labels/${annotationIndex}?split=${split}`, {
		method: "PATCH",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({ new_class_id: newClassId })
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Reclassify failed: ${res.statusText}`);
	}
	return res.json();
}
async function deleteAnnotation(datasetId, filename, annotationIndex, split = "train") {
	const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/images/${encodeURIComponent(filename)}/labels/${annotationIndex}?split=${split}`, { method: "DELETE" });
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Delete failed: ${res.statusText}`);
	}
	return res.json();
}
async function fetchAvailableInspections(limit = 50) {
	const res = await fetch(`${API_BASE}/api/import/inspections?limit=${limit}`);
	if (!res.ok) throw new Error(`Failed to fetch inspections: ${res.statusText}`);
	return res.json();
}
async function importInspectionToDataset(datasetId, inspectionId, split = "train") {
	const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/import/inspection`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({
			inspection_id: inspectionId,
			split
		})
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Import failed: ${res.statusText}`);
	}
	return res.json();
}
async function createNewDataset(versionName, stage, notes = null) {
	const res = await fetch(`${API_BASE}/api/datasets/create`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify({
			version_name: versionName,
			stage,
			notes
		})
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Create dataset failed: ${res.statusText}`);
	}
	return res.json();
}
async function importZipToDataset(datasetId, file, split = "train") {
	const formData = new FormData();
	formData.append("file", file);
	formData.append("split", split);
	const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/import/zip`, {
		method: "POST",
		body: formData
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `ZIP import failed: ${res.statusText}`);
	}
	return res.json();
}
async function deleteDataset(datasetId) {
	const res = await fetch(`${API_BASE}/api/datasets/${datasetId}`, { method: "DELETE" });
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to delete dataset: ${res.statusText}`);
	}
}
async function importDatasetZip(file, versionName) {
	const formData = new FormData();
	formData.append("file", file);
	formData.append("version_name", versionName);
	const res = await fetch(`${API_BASE}/api/datasets/import-dataset`, {
		method: "POST",
		body: formData
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Import dataset failed: ${res.statusText}`);
	}
	return res.json();
}
async function fetchSplitStructure(datasetId) {
	const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/split-structure`);
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Split detection failed: ${res.statusText}`);
	}
	return res.json();
}
async function resplitDataset(datasetId, request) {
	const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/resplit`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(request)
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Resplit failed: ${res.statusText}`);
	}
	return res.json();
}
async function tileDataset(datasetId, request) {
	const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/tile`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(request)
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Tiling failed: ${res.statusText}`);
	}
	return res.json();
}
async function launchTrainingJob(request) {
	const res = await fetch(`${API_BASE}/api/training/jobs`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(request)
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to launch training job: ${res.statusText}`);
	}
	return res.json();
}
async function fetchTrainingJobs(limit = 50, offset = 0) {
	const res = await fetch(`${API_BASE}/api/training/jobs?limit=${limit}&offset=${offset}`);
	if (!res.ok) throw new Error(`Failed to fetch training jobs: ${res.statusText}`);
	return res.json();
}
async function fetchTrainingJobDetail(jobId) {
	const res = await fetch(`${API_BASE}/api/training/jobs/${jobId}`);
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to fetch job detail: ${res.statusText}`);
	}
	return res.json();
}
async function fetchTrainingJobLogs(jobId) {
	const res = await fetch(`${API_BASE}/api/training/jobs/${jobId}/logs`);
	if (!res.ok) throw new Error(`Failed to fetch logs: ${res.statusText}`);
	return res.text();
}
async function stopTrainingJob(jobId) {
	const res = await fetch(`${API_BASE}/api/training/jobs/${jobId}/stop`, { method: "POST" });
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to stop job: ${res.statusText}`);
	}
	return res.json();
}
async function fetchConfigTemplate(stage) {
	const res = await fetch(`${API_BASE}/api/training/config-template?stage=${stage}`);
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to fetch template: ${res.statusText}`);
	}
	return res.json();
}
async function fetchExperiments() {
	const res = await fetch(`${API_BASE}/api/experiments`);
	if (!res.ok) throw new Error(`Failed to fetch experiments: ${res.statusText}`);
	return res.json();
}
async function fetchExperimentRuns(experimentId) {
	const res = await fetch(`${API_BASE}/api/experiments/${experimentId}/runs`);
	if (!res.ok) throw new Error(`Failed to fetch runs: ${res.statusText}`);
	return res.json();
}
async function fetchModelRegistryModels(stage, status) {
	let url = `${API_BASE}/api/model-registry`;
	const params = new URLSearchParams();
	if (stage) params.set("stage", stage);
	if (status) params.set("status", status);
	if (params.toString()) url += `?${params.toString()}`;
	const res = await fetch(url);
	if (!res.ok) throw new Error(`Failed to fetch model registry: ${res.statusText}`);
	return res.json();
}
async function evaluateModelGates(modelId) {
	const res = await fetch(`${API_BASE}/api/model-registry/${modelId}/evaluate`, { method: "POST" });
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to evaluate gates: ${res.statusText}`);
	}
	return res.json();
}
async function promoteModel(modelId) {
	const res = await fetch(`${API_BASE}/api/model-registry/${modelId}/promote`, { method: "POST" });
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to promote model: ${res.statusText}`);
	}
	return res.json();
}
async function deployModel(modelId) {
	const res = await fetch(`${API_BASE}/api/model-registry/${modelId}/deploy`, { method: "POST" });
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to deploy model: ${res.statusText}`);
	}
	return res.json();
}
async function rollbackModel(stage) {
	const res = await fetch(`${API_BASE}/api/model-registry/stage/${stage}/rollback`, { method: "POST" });
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to rollback model: ${res.statusText}`);
	}
	return res.json();
}
async function listTaxonomies(stage) {
	let url = `${API_BASE}/api/taxonomies`;
	const params = new URLSearchParams();
	if (stage) params.set("stage", stage);
	if (params.toString()) url += `?${params.toString()}`;
	const res = await fetch(url);
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to list taxonomies: ${res.statusText}`);
	}
	return res.json();
}
async function createTaxonomy(req) {
	const res = await fetch(`${API_BASE}/api/taxonomies`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(req)
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to create taxonomy: ${res.statusText}`);
	}
	return res.json();
}
async function updateTaxonomy(id, req) {
	const res = await fetch(`${API_BASE}/api/taxonomies/${id}`, {
		method: "PATCH",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(req)
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to update taxonomy: ${res.statusText}`);
	}
	return res.json();
}
async function deleteTaxonomy(id) {
	const res = await fetch(`${API_BASE}/api/taxonomies/${id}`, { method: "DELETE" });
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to delete taxonomy: ${res.statusText}`);
	}
}
async function listCheckpoints(stage) {
	let url = `${API_BASE}/api/checkpoints`;
	const params = new URLSearchParams();
	if (stage) params.set("stage", stage);
	if (params.toString()) url += `?${params.toString()}`;
	const res = await fetch(url);
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to list checkpoints: ${res.statusText}`);
	}
	return res.json();
}
async function scanCheckpoints() {
	const res = await fetch(`${API_BASE}/api/checkpoints/scan`, { method: "POST" });
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to scan checkpoints: ${res.statusText}`);
	}
	return res.json();
}
async function registerCheckpoint(req) {
	const res = await fetch(`${API_BASE}/api/checkpoints/register`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(req)
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to register checkpoint: ${res.statusText}`);
	}
	return res.json();
}
async function deleteCheckpoint(id) {
	const res = await fetch(`${API_BASE}/api/checkpoints/${id}`, { method: "DELETE" });
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to delete checkpoint: ${res.statusText}`);
	}
}
async function startSurgery(req) {
	const res = await fetch(`${API_BASE}/api/surgery`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(req)
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to start surgery: ${res.statusText}`);
	}
	return res.json();
}
async function getSurgeryStatus(jobId) {
	const res = await fetch(`${API_BASE}/api/surgery/${jobId}`);
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to get surgery status: ${res.statusText}`);
	}
	return res.json();
}
async function listRecipes(stage) {
	let url = `${API_BASE}/api/recipes`;
	const params = new URLSearchParams();
	if (stage) params.set("stage", stage);
	if (params.toString()) url += `?${params.toString()}`;
	const res = await fetch(url);
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to list recipes: ${res.statusText}`);
	}
	return res.json();
}
async function listRecipePresets() {
	const res = await fetch(`${API_BASE}/api/recipes/presets`);
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to list presets: ${res.statusText}`);
	}
	return res.json();
}
async function createRecipe(req) {
	const res = await fetch(`${API_BASE}/api/recipes`, {
		method: "POST",
		headers: { "Content-Type": "application/json" },
		body: JSON.stringify(req)
	});
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to create recipe: ${res.statusText}`);
	}
	return res.json();
}
async function deleteRecipe(id) {
	const res = await fetch(`${API_BASE}/api/recipes/${id}`, { method: "DELETE" });
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to delete recipe: ${res.statusText}`);
	}
}
async function listChains() {
	const res = await fetch(`${API_BASE}/api/chains`);
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to list chains: ${res.statusText}`);
	}
	return res.json();
}
async function startChainRun(chainId) {
	const res = await fetch(`${API_BASE}/api/chains/${chainId}/run`, { method: "POST" });
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to start chain run: ${res.statusText}`);
	}
	return res.json();
}
async function getChainRunStatus(runId) {
	const res = await fetch(`${API_BASE}/api/chains/runs/${runId}`);
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to get chain run status: ${res.statusText}`);
	}
	return res.json();
}
async function runFullDatasetAudit(datasetId) {
	const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/audit/full`, { method: "POST" });
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to run full audit: ${res.statusText}`);
	}
	return res.json();
}
async function fetchDatasetAuditReport(datasetId) {
	const res = await fetch(`${API_BASE}/api/datasets/${datasetId}/audit/report`);
	if (res.status === 404) return null;
	if (!res.ok) {
		const err = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error(err.detail || `Failed to fetch audit report: ${res.statusText}`);
	}
	return res.json();
}
//#endregion
export { startChainRun as $, fetchTrainingJobLogs as A, listCheckpoints as B, fetchHostProfile as C, fetchSystemDevices as D, fetchSplitStructure as E, importDatasetZip as F, reclassifyAnnotation as G, listRecipes as H, importInspectionToDataset as I, rollbackModel as J, registerCheckpoint as K, importZipToDataset as L, getChainRunStatus as M, getDatasetImageUrl as N, fetchSystemMetrics as O, getSurgeryStatus as P, scanCheckpoints as Q, launchTrainingJob as R, fetchExperiments as S, fetchReviewQueue as T, listTaxonomies as U, listRecipePresets as V, promoteModel as W, runInspection as X, runFullDatasetAudit as Y, runLeakageAudit as Z, fetchDatasetDetail as _, deleteAnnotation as a, updateTaxonomy as at, fetchDatasets as b, deleteRecipe as c, deployModel as d, startSurgery as et, evaluateModelGates as f, fetchDatasetAuditReport as g, fetchConfigTemplate as h, createTaxonomy as i, updateReview as it, fetchTrainingJobs as j, fetchTrainingJobDetail as k, deleteReview as l, fetchAvailableInspections as m, createNewDataset as n, submitReview as nt, deleteCheckpoint as o, fetchAllReviews as p, resplitDataset as q, createRecipe as r, tileDataset as rt, deleteDataset as s, buildDataset as t, stopTrainingJob as tt, deleteTaxonomy as u, fetchDatasetImageLabels as v, fetchModelRegistryModels as w, fetchExperimentRuns as x, fetchDatasetImages as y, listChains as z };
