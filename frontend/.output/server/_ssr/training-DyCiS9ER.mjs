import { n as __toESM } from "../_runtime.mjs";
import { $ as startChainRun, A as fetchTrainingJobLogs, H as listRecipes, M as getChainRunStatus, R as launchTrainingJob, V as listRecipePresets, b as fetchDatasets, c as deleteRecipe, h as fetchConfigTemplate, j as fetchTrainingJobs, k as fetchTrainingJobDetail, r as createRecipe, tt as stopTrainingJob, z as listChains } from "./apiClient-ClfACpV5.mjs";
import { t as cn } from "./utils-C_uf36nf.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { j as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { t as Button } from "./button-BkEeRci-.mjs";
import { l as StatusBadge } from "./alert-dialog-DsQ-Uqlb.mjs";
import { t as ConfirmDialog } from "./ConfirmDialog-CbIeVXtH.mjs";
import { E as FileText, I as CircleX, J as ArrowLeft, L as CircleCheck, h as Play, m as Plus, o as Trash2, p as RefreshCw, s as Square, v as LoaderCircle } from "../_libs/lucide-react.mjs";
import { a as DialogHeader, i as DialogFooter, n as DialogContent, o as DialogTitle, r as DialogDescription, s as EmptyState, t as Dialog } from "./dialog-BTaDPjwY.mjs";
import { i as CardTitle, n as CardContent, r as CardHeader, t as Card } from "./card-BXjpJ96D.mjs";
import { n as toast } from "../_libs/sonner.mjs";
import { n as PageShell, t as PageHeader } from "./PageShell-CQ88Jn3b.mjs";
import { a as SelectTrigger, i as SelectItem, n as Select, o as SelectValue, r as SelectContent, t as Label } from "./label-CsQhRIhI.mjs";
import { a as TabsList, i as TabsContent, n as Input, o as TabsTrigger, r as Tabs, s as TaxonomyPicker, t as CheckpointPicker } from "./tabs-DtPBE-s0.mjs";
import { t as Badge } from "./badge-D1Dupn2y.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/training-DyCiS9ER.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function RecipeLaunchForm({ onClose, onLaunched }) {
	const [recipes, setRecipes] = (0, import_react.useState)([]);
	const [datasets, setDatasets] = (0, import_react.useState)([]);
	const [loading, setLoading] = (0, import_react.useState)(true);
	const [recipeId, setRecipeId] = (0, import_react.useState)("");
	const [datasetId, setDatasetId] = (0, import_react.useState)("");
	const [checkpointOverride, setCheckpointOverride] = (0, import_react.useState)(null);
	const [submitting, setSubmitting] = (0, import_react.useState)(false);
	const [error, setError] = (0, import_react.useState)(null);
	(0, import_react.useEffect)(() => {
		Promise.all([listRecipes(), fetchDatasets()]).then(([r, d]) => {
			setRecipes(r.recipes);
			setDatasets(d.datasets);
		}).catch(() => setError("Failed to load recipes or datasets")).finally(() => setLoading(false));
	}, []);
	const recipe = recipes.find((r) => r.id === recipeId) ?? null;
	const stageDatasets = (0, import_react.useMemo)(() => recipe ? datasets.filter((d) => d.stage === recipe.stage) : datasets, [datasets, recipe]);
	const isChainOnly = recipe?.base_strategy === "from_previous_step";
	const needsCheckpoint = recipe?.base_strategy === "from_checkpoint" && !recipe.base_checkpoint_id;
	const canLaunch = recipe != null && datasetId !== "" && !isChainOnly && (!needsCheckpoint || checkpointOverride != null);
	const handleLaunch = async () => {
		if (!recipe) return;
		setSubmitting(true);
		setError(null);
		const request = {
			stage: recipe.stage,
			dataset_id: datasetId,
			recipe_id: recipe.id,
			base_checkpoint_id: checkpointOverride ?? void 0
		};
		try {
			await launchTrainingJob(request);
			onLaunched();
			onClose();
		} catch (e) {
			setError(e instanceof Error ? e.message : "Failed to launch job");
		} finally {
			setSubmitting(false);
		}
	};
	if (loading) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
		className: "text-xs text-muted-foreground",
		children: "Loading recipes..."
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-3",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1.5",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
					className: "text-sm font-medium",
					children: "Recipe"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("select", {
					value: recipeId,
					onChange: (e) => {
						setRecipeId(e.target.value);
						setDatasetId("");
						setCheckpointOverride(null);
					},
					className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
						value: "",
						children: "Select a recipe..."
					}), recipes.map((r) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("option", {
						value: r.id,
						children: [
							r.name,
							" (",
							r.stage,
							")"
						]
					}, r.id))]
				})]
			}),
			recipe && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
				className: "font-mono text-[10px] text-muted-foreground",
				children: [
					"freeze: ",
					recipe.freeze_mode,
					" · lr: ",
					recipe.lr_mode,
					" · loss: ",
					recipe.loss_type,
					" · epochs:",
					" ",
					recipe.epochs,
					" · imgsz: ",
					recipe.imgsz
				]
			}),
			isChainOnly && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-400",
				children: "This recipe uses base_strategy \"from_previous_step\" and can only run inside a chain."
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1.5",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
					className: "text-sm font-medium",
					children: "Dataset"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("select", {
					value: datasetId,
					onChange: (e) => setDatasetId(e.target.value),
					className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
						value: "",
						children: "Select a dataset..."
					}), stageDatasets.map((d) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("option", {
						value: d.dataset_id,
						children: [
							d.name,
							" (",
							d.stage,
							")"
						]
					}, d.dataset_id))]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1.5",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "text-xs font-medium text-muted-foreground",
						children: "Base checkpoint override (optional)"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CheckpointPicker, {
						stage: recipe?.stage,
						value: checkpointOverride,
						onChange: setCheckpointOverride
					}),
					needsCheckpoint && checkpointOverride == null && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-[10px] text-amber-600 dark:text-amber-400",
						children: "Recipe has no base checkpoint — select one to launch."
					})
				]
			}),
			recipe && recipe.epochs > 5 && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-400",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "⚠️ Long Training Detected:" }),
					" ",
					recipe.epochs,
					" epochs may take several hours on Mac. The Mac safety guard clamps to 1 epoch unless overridden server-side."
				]
			}),
			error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-xs text-destructive",
				children: error
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex justify-end gap-2 pt-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "ghost",
					onClick: onClose,
					children: "Cancel"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					onClick: handleLaunch,
					disabled: !canLaunch || submitting,
					children: submitting ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "mr-1.5 h-4 w-4 animate-spin" }), " Launching..."] }) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Play, { className: "mr-1.5 h-4 w-4" }), " Launch Recipe"] })
				})]
			})
		]
	});
}
function LaunchTrainingDialog({ onClose, onLaunched }) {
	const [datasets, setDatasets] = (0, import_react.useState)([]);
	const [loadingDatasets, setLoadingDatasets] = (0, import_react.useState)(true);
	const [mode, setMode] = (0, import_react.useState)("direct");
	const [stage, setStage] = (0, import_react.useState)("stage2");
	(0, import_react.useEffect)(() => {
		handleLoadTemplate();
	}, [stage]);
	const [datasetPath, setDatasetPath] = (0, import_react.useState)("");
	const [configPath, setConfigPath] = (0, import_react.useState)("");
	const [baseModel, setBaseModel] = (0, import_react.useState)("");
	const [device, setDevice] = (0, import_react.useState)("0");
	const [projectName, setProjectName] = (0, import_react.useState)("");
	const [runName, setRunName] = (0, import_react.useState)("");
	const [epochs, setEpochs] = (0, import_react.useState)(100);
	const [imgsz, setImgsz] = (0, import_react.useState)(640);
	const [batchSize, setBatchSize] = (0, import_react.useState)(8);
	const [showAdvanced, setShowAdvanced] = (0, import_react.useState)(false);
	const [advancedJson, setAdvancedJson] = (0, import_react.useState)("{}");
	const [submitting, setSubmitting] = (0, import_react.useState)(false);
	const [loadingTemplate, setLoadingTemplate] = (0, import_react.useState)(false);
	const [error, setError] = (0, import_react.useState)(null);
	(0, import_react.useEffect)(() => {
		fetchDatasets().then((res) => {
			setDatasets(res.datasets);
			if (res.datasets.length > 0) setDatasetPath(res.datasets[0].yaml_path);
		}).catch(() => setError("Failed to load datasets")).finally(() => setLoadingDatasets(false));
	}, []);
	const handleLoadTemplate = async () => {
		setLoadingTemplate(true);
		setError(null);
		try {
			const tmpl = (await fetchConfigTemplate(stage)).template;
			if (tmpl.project_name) setProjectName(tmpl.project_name);
			if (tmpl.run_name) setRunName(tmpl.run_name);
			if (tmpl.model_preset) setBaseModel(tmpl.model_preset);
			if (tmpl.device) setDevice(String(tmpl.device));
			if (tmpl.epochs) setEpochs(tmpl.epochs);
			if (tmpl.imgsz) setImgsz(tmpl.imgsz);
			if (tmpl.batch_size) setBatchSize(tmpl.batch_size);
			const { epochs: _, imgsz: __, batch_size: ___, ...rest } = tmpl;
			if (Object.keys(rest).length > 0) {
				setShowAdvanced(true);
				setAdvancedJson(JSON.stringify(rest, null, 2));
			}
		} catch (e) {
			setError(e instanceof Error ? e.message : "Failed to load template");
		} finally {
			setLoadingTemplate(false);
		}
	};
	const handleLaunch = async () => {
		if (!datasetPath) {
			setError("Please select a dataset.");
			return;
		}
		const overrides = {};
		if (epochs !== "") overrides.epochs = epochs;
		if (imgsz !== "") overrides.imgsz = imgsz;
		if (batchSize !== "") overrides.batch_size = batchSize;
		if (showAdvanced && advancedJson.trim()) try {
			const advanced = JSON.parse(advancedJson);
			Object.assign(overrides, advanced);
		} catch {
			setError("Invalid JSON in Advanced Overrides field.");
			return;
		}
		setSubmitting(true);
		setError(null);
		const request = {
			stage,
			dataset_path: datasetPath,
			config_path: configPath || void 0,
			base_model: baseModel || void 0,
			device,
			project_name: projectName || void 0,
			run_name: runName || void 0,
			overrides
		};
		try {
			await launchTrainingJob(request);
			onLaunched();
			onClose();
		} catch (e) {
			setError(e instanceof Error ? e.message : "Failed to launch job");
		} finally {
			setSubmitting(false);
		}
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dialog, {
		open: true,
		onOpenChange: (o) => {
			if (!o) onClose();
		},
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, {
			className: "max-w-lg max-h-[90vh] overflow-y-auto space-y-4",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogHeader, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle, { children: "Launch Training Job" }) }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "grid grid-cols-2 gap-1 rounded-md border border-border p-1",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						type: "button",
						onClick: () => setMode("direct"),
						className: mode === "direct" ? "rounded-sm bg-muted px-3 py-1.5 text-xs font-medium" : "rounded-sm px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground",
						children: "Direct config"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						type: "button",
						onClick: () => setMode("recipe"),
						className: mode === "recipe" ? "rounded-sm bg-muted px-3 py-1.5 text-xs font-medium" : "rounded-sm px-3 py-1.5 text-xs text-muted-foreground hover:text-foreground",
						children: "Recipe"
					})]
				}),
				mode === "recipe" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(RecipeLaunchForm, {
					onClose,
					onLaunched
				}),
				mode === "direct" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "space-y-3",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-1.5",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "flex items-center justify-between",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
										className: "text-sm font-medium",
										children: "Stage"
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
										type: "button",
										onClick: handleLoadTemplate,
										disabled: loadingTemplate,
										className: "text-xs text-primary hover:underline flex items-center gap-1",
										children: loadingTemplate ? "Loading..." : "Load Champion Defaults"
									})]
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("select", {
									value: stage,
									onChange: (e) => setStage(e.target.value),
									className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
									children: [
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
											value: "stage1",
											children: "Stage 1 (SOD / Anomaly)"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
											value: "stage2",
											children: "Stage 2 (7-class Defect)"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
											value: "stage3",
											children: "Stage 3 (21-class Panel)"
										})
									]
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-1.5",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
									className: "text-sm font-medium",
									children: "Dataset"
								}), loadingDatasets ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-xs text-muted-foreground",
									children: "Loading datasets..."
								}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("select", {
									value: datasetPath,
									onChange: (e) => setDatasetPath(e.target.value),
									className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm font-mono",
									children: datasets.map((d) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("option", {
										value: d.yaml_path,
										children: [
											d.name,
											" (",
											d.stage,
											")"
										]
									}, d.dataset_id))
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "grid grid-cols-2 gap-3",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-1.5",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
										className: "text-xs font-medium text-muted-foreground",
										children: "Config Path (Optional)"
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
										type: "text",
										value: configPath,
										onChange: (e) => setConfigPath(e.target.value),
										placeholder: "configs/stage2/train.yaml",
										className: "w-full rounded-md border border-input bg-background px-3 py-2 text-xs font-mono"
									})]
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-1.5",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
										className: "text-xs font-medium text-muted-foreground",
										children: "Base Model (Optional)"
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
										type: "text",
										value: baseModel,
										onChange: (e) => setBaseModel(e.target.value),
										placeholder: "yolo26m-seg.pt",
										className: "w-full rounded-md border border-input bg-background px-3 py-2 text-xs font-mono"
									})]
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "grid grid-cols-3 gap-3",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
										className: "space-y-1.5",
										children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
											className: "text-xs font-medium text-muted-foreground",
											children: "Device"
										}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
											type: "text",
											value: device,
											onChange: (e) => setDevice(e.target.value),
											placeholder: "0",
											className: "w-full rounded-md border border-input bg-background px-3 py-2 text-xs font-mono"
										})]
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
										className: "space-y-1.5",
										children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
											className: "text-xs font-medium text-muted-foreground",
											children: "Project Name"
										}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
											type: "text",
											value: projectName,
											onChange: (e) => setProjectName(e.target.value),
											placeholder: "stage2_exp",
											className: "w-full rounded-md border border-input bg-background px-3 py-2 text-xs"
										})]
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
										className: "space-y-1.5",
										children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
											className: "text-xs font-medium text-muted-foreground",
											children: "Run Name"
										}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
											type: "text",
											value: runName,
											onChange: (e) => setRunName(e.target.value),
											placeholder: "run_01",
											className: "w-full rounded-md border border-input bg-background px-3 py-2 text-xs"
										})]
									})
								]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "grid grid-cols-3 gap-3",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
										className: "space-y-1.5",
										children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
											className: "text-xs font-medium text-muted-foreground",
											children: "Epochs"
										}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
											type: "number",
											min: 1,
											value: epochs,
											onChange: (e) => setEpochs(e.target.value === "" ? "" : Number(e.target.value)),
											className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
										})]
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
										className: "space-y-1.5",
										children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
											className: "text-xs font-medium text-muted-foreground",
											children: "Image Size"
										}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
											type: "number",
											min: 32,
											step: 32,
											value: imgsz,
											onChange: (e) => setImgsz(e.target.value === "" ? "" : Number(e.target.value)),
											className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
										})]
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
										className: "space-y-1.5",
										children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
											className: "text-xs font-medium text-muted-foreground",
											children: "Batch Size"
										}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
											type: "number",
											min: 1,
											value: batchSize,
											onChange: (e) => setBatchSize(e.target.value === "" ? "" : Number(e.target.value)),
											className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
										})]
									})
								]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-1.5",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
									type: "button",
									onClick: () => setShowAdvanced(!showAdvanced),
									className: "text-xs text-primary hover:underline",
									children: [showAdvanced ? "Hide" : "Show", " Advanced Overrides (JSON)"]
								}), showAdvanced && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("textarea", {
									value: advancedJson,
									onChange: (e) => setAdvancedJson(e.target.value),
									placeholder: "{\"lr0\": 0.01, \"momentum\": 0.937}",
									className: "w-full rounded-md border border-input bg-background px-3 py-2 text-xs font-mono min-h-[80px]"
								})]
							})
						]
					}),
					error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-xs text-destructive",
						children: error
					}),
					(() => {
						const currentEpochs = typeof epochs === "number" ? epochs : 100;
						if (currentEpochs > 5) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-400",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "⚠️ Long Training Detected:" }),
								" ",
								currentEpochs,
								" epochs may take several hours on Mac. Consider reducing to 1-5 epochs for testing, or use a remote GPU server."
							]
						});
						return null;
					})(),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex justify-end gap-2 pt-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							onClick: onClose,
							children: "Cancel"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							onClick: handleLaunch,
							disabled: submitting || !datasetPath,
							children: submitting ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "mr-1.5 h-4 w-4 animate-spin" }), " Launching..."] }) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Play, { className: "mr-1.5 h-4 w-4" }), " Launch Job"] })
						})]
					})
				] })
			]
		})
	});
}
var STATUS_TONES = {
	pending: "gray",
	running: "blue",
	completed: "green",
	failed: "red",
	cancelled: "yellow"
};
function formatDate(iso) {
	if (!iso) return "-";
	return new Date(iso).toLocaleString();
}
function JobListTable({ jobs, loading, onSelectJob, onStopJob }) {
	if (loading) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex items-center justify-center p-8 text-muted-foreground",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "mr-2 h-4 w-4 animate-spin" }), " Loading jobs..."]
	});
	if (jobs.length === 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, {
		title: "No training jobs found",
		hint: "Launch one to get started."
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "overflow-x-auto rounded-lg border border-border",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", {
			className: "w-full text-sm",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", {
				className: "bg-muted/50 text-xs uppercase tracking-wider text-muted-foreground",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-4 py-3 text-left font-medium",
						children: "ID"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-4 py-3 text-left font-medium",
						children: "Stage"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-4 py-3 text-left font-medium",
						children: "Status"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-4 py-3 text-left font-medium",
						children: "Project / Run"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-4 py-3 text-left font-medium",
						children: "Created"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-4 py-3 text-right font-medium",
						children: "Actions"
					})
				] })
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", {
				className: "divide-y divide-border bg-card",
				children: jobs.map((job) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
					className: "hover:bg-muted/30 transition-colors cursor-pointer",
					onClick: () => onSelectJob(job),
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("td", {
							className: "px-4 py-3 font-mono text-xs",
							children: [job.id.substring(0, 8), "..."]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-4 py-3 capitalize",
							children: job.stage
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-4 py-3",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatusBadge, {
								tone: STATUS_TONES[job.status],
								size: "md",
								icon: job.status === "running" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-3 w-3 animate-spin" }) : void 0,
								children: job.status
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("td", {
							className: "px-4 py-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "font-medium",
								children: job.project_name
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
								className: "text-xs text-muted-foreground",
								children: job.run_name
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-4 py-3 text-xs text-muted-foreground",
							children: formatDate(job.created_at)
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-4 py-3 text-right",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "flex justify-end gap-2",
								onClick: (e) => e.stopPropagation(),
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
									variant: "ghost",
									size: "sm",
									onClick: () => onSelectJob(job),
									title: "View Logs",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(FileText, { className: "h-4 w-4" })
								}), job.status === "running" || job.status === "pending" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
									variant: "destructive",
									size: "sm",
									onClick: () => onStopJob(job.id),
									title: "Stop Job",
									children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Square, { className: "h-4 w-4" })
								}) : null]
							})
						})
					]
				}, job.id))
			})]
		})
	});
}
var STATUS_STYLES = {
	pending: "bg-gray-500/15 text-gray-700 dark:text-gray-400 border-gray-500/30",
	running: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30",
	completed: "bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/30",
	failed: "bg-red-500/15 text-red-700 dark:text-red-400 border-red-500/30",
	cancelled: "bg-yellow-500/15 text-yellow-700 dark:text-yellow-400 border-yellow-500/30"
};
function JobDetailPanel({ jobId, onBack }) {
	const [job, setJob] = (0, import_react.useState)(null);
	const [logs, setLogs] = (0, import_react.useState)("");
	const [loading, setLoading] = (0, import_react.useState)(true);
	const [error, setError] = (0, import_react.useState)(null);
	const logEndRef = (0, import_react.useRef)(null);
	const loadData = async () => {
		try {
			setLoading(true);
			setError(null);
			const [jobDetail, jobLogs] = await Promise.all([fetchTrainingJobDetail(jobId), fetchTrainingJobLogs(jobId)]);
			setJob(jobDetail);
			setLogs(jobLogs);
		} catch (err) {
			setError(err.message || "Failed to load job details");
		} finally {
			setLoading(false);
		}
	};
	(0, import_react.useEffect)(() => {
		loadData();
		const interval = setInterval(() => {
			if (job && (job.status === "running" || job.status === "pending")) loadData();
		}, 3e3);
		return () => clearInterval(interval);
	}, [jobId, job?.status]);
	(0, import_react.useEffect)(() => {
		if (logEndRef.current) logEndRef.current.scrollIntoView({ behavior: "smooth" });
	}, [logs]);
	const handleStop = async () => {
		if (!window.confirm("Are you sure you want to terminate this training job?")) return;
		try {
			await stopTrainingJob(jobId);
			loadData();
		} catch (err) {
			alert(`Failed to stop job: ${err.message}`);
		}
	};
	if (loading && !job) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "p-8 text-center text-muted-foreground",
		children: "Loading job details..."
	});
	if (error) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "p-8 text-center text-destructive",
		children: ["Error: ", error]
	});
	if (!job) return null;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
					onClick: onBack,
					className: "text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ArrowLeft, { className: "h-4 w-4" }), " Back to jobs"]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
						variant: "outline",
						size: "sm",
						onClick: loadData,
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(RefreshCw, { className: "h-4 w-4 mr-1.5" }), " Refresh"]
					}), (job.status === "running" || job.status === "pending") && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
						variant: "destructive",
						size: "sm",
						onClick: handleStop,
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Square, { className: "h-4 w-4 mr-1.5" }), " Stop Job"]
					})]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "rounded-lg border border-border bg-card p-4 space-y-3",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center justify-between",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h2", {
							className: "text-lg font-semibold font-mono",
							children: [
								job.project_name,
								" / ",
								job.run_name
							]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: `px-2 py-0.5 rounded-full text-xs font-medium border capitalize ${STATUS_STYLES[job.status] || STATUS_STYLES.pending}`,
							children: job.status
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid grid-cols-2 md:grid-cols-4 gap-4 text-sm",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs text-muted-foreground",
								children: "Stage"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "font-medium capitalize",
								children: job.stage
							})] }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs text-muted-foreground",
								children: "Device"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "font-medium",
								children: job.device
							})] }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs text-muted-foreground",
								children: "Created"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "font-medium",
								children: new Date(job.created_at).toLocaleString()
							})] }),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs text-muted-foreground",
								children: "Dataset"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "font-medium truncate",
								title: job.dataset_path,
								children: job.dataset_path.split("/").pop()
							})] })
						]
					}),
					job.error_message && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-700 dark:text-red-400",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("strong", { children: "Error:" }),
							" ",
							job.error_message
						]
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "rounded-lg border border-border bg-black/90 text-green-400 font-mono text-xs overflow-hidden",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "bg-black/50 px-4 py-2 border-b border-white/10 text-gray-300 flex items-center justify-between",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: "Training Logs" }), job.status === "running" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-3 w-3 animate-spin" })]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "p-4 h-[500px] overflow-y-auto whitespace-pre-wrap break-words",
					children: [logs || "No logs available yet...", /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { ref: logEndRef })]
				})]
			})
		]
	});
}
function StrategyPresetPicker({ onSelect }) {
	const [presets, setPresets] = (0, import_react.useState)([]);
	const [loading, setLoading] = (0, import_react.useState)(true);
	(0, import_react.useEffect)(() => {
		listRecipePresets().then((res) => setPresets(res.recipes)).catch(() => setPresets([])).finally(() => setLoading(false));
	}, []);
	if (loading) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
		className: "text-sm text-muted-foreground",
		children: "Loading presets..."
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "grid grid-cols-1 gap-4 md:grid-cols-2",
		children: presets.map((preset) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
			className: "cursor-pointer transition hover:border-primary",
			onClick: () => onSelect(preset),
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardHeader, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardTitle, {
				className: "text-sm",
				children: preset.name
			}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(CardContent, { children: [preset.description && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "mb-3 text-xs text-muted-foreground",
				children: preset.description
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("dl", {
				className: "space-y-1 text-xs",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex justify-between",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dt", {
							className: "text-muted-foreground",
							children: "Freeze:"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
							className: "font-mono",
							children: preset.freeze_mode
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex justify-between",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dt", {
							className: "text-muted-foreground",
							children: "LR mode:"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
							className: "font-mono",
							children: preset.lr_mode
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex justify-between",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dt", {
							className: "text-muted-foreground",
							children: "Loss:"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
							className: "font-mono",
							children: preset.loss_type
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex justify-between",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dt", {
							className: "text-muted-foreground",
							children: "Epochs:"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
							className: "font-mono",
							children: preset.epochs
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex justify-between",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dt", {
							className: "text-muted-foreground",
							children: "imgsz:"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
							className: "font-mono",
							children: preset.imgsz
						})]
					})
				]
			})] })]
		}, preset.id))
	});
}
var Textarea = import_react.forwardRef(({ className, ...props }, ref) => {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("textarea", {
		className: cn("flex min-h-[60px] w-full rounded-md border border-input bg-transparent px-3 py-2 text-base shadow-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm", className),
		ref,
		...props
	});
});
Textarea.displayName = "Textarea";
function RecipeBuilder({ open, onOpenChange, preset, onSaved }) {
	const [name, setName] = (0, import_react.useState)(preset?.name ?? "");
	const [description, setDescription] = (0, import_react.useState)(preset?.description ?? "");
	const [taxonomyId, setTaxonomyId] = (0, import_react.useState)(preset?.taxonomy_id ?? null);
	const [baseStrategy, setBaseStrategy] = (0, import_react.useState)(preset?.base_strategy ?? "from_checkpoint");
	const [baseCheckpointId, setBaseCheckpointId] = (0, import_react.useState)(preset?.base_checkpoint_id ?? null);
	const [freezeMode, setFreezeMode] = (0, import_react.useState)(preset?.freeze_mode ?? "none");
	const [freezeLayers, setFreezeLayers] = (0, import_react.useState)(preset?.freeze_layers ?? null);
	const [lrMode, setLrMode] = (0, import_react.useState)(preset?.lr_mode ?? "uniform");
	const [splitLayerIdx, setSplitLayerIdx] = (0, import_react.useState)(preset?.split_layer_idx ?? null);
	const [backboneLrMult, setBackboneLrMult] = (0, import_react.useState)(preset?.backbone_lr_mult ?? null);
	const [lossType, setLossType] = (0, import_react.useState)(preset?.loss_type ?? "bce");
	const [flGamma, setFlGamma] = (0, import_react.useState)(preset?.fl_gamma ?? 2);
	const [flAlpha, setFlAlpha] = (0, import_react.useState)(preset?.fl_alpha ?? .5);
	const [flScale, setFlScale] = (0, import_react.useState)(preset?.fl_scale ?? 1);
	const [imgsz, setImgsz] = (0, import_react.useState)(preset?.imgsz ?? 640);
	const [batchSize, setBatchSize] = (0, import_react.useState)(preset?.batch_size ?? 8);
	const [epochs, setEpochs] = (0, import_react.useState)(preset?.epochs ?? 100);
	const [optimizer, setOptimizer] = (0, import_react.useState)(preset?.optimizer ?? "SGD");
	const [lr0, setLr0] = (0, import_react.useState)(preset?.lr0 ?? .01);
	const [lrf, setLrf] = (0, import_react.useState)(preset?.lrf ?? .01);
	const [patience, setPatience] = (0, import_react.useState)(preset?.patience ?? 20);
	const [saving, setSaving] = (0, import_react.useState)(false);
	async function handleSave() {
		if (!name.trim() || !taxonomyId) {
			toast.error("Name and taxonomy are required");
			return;
		}
		setSaving(true);
		try {
			await createRecipe({
				name: name.trim(),
				taxonomy_id: taxonomyId,
				description: description.trim() || null,
				base_strategy: baseStrategy,
				base_checkpoint_id: baseCheckpointId,
				freeze_mode: freezeMode,
				freeze_layers: freezeMode !== "none" ? freezeLayers : null,
				lr_mode: lrMode,
				split_layer_idx: lrMode === "differential" ? splitLayerIdx : null,
				backbone_lr_mult: lrMode === "differential" ? backboneLrMult : null,
				loss_type: lossType,
				fl_gamma: flGamma,
				fl_alpha: flAlpha,
				fl_scale: flScale,
				imgsz,
				batch_size: batchSize,
				epochs,
				optimizer,
				lr0,
				lrf,
				patience,
				augmentations: null
			});
			toast.success("Recipe created");
			onSaved?.();
			onOpenChange(false);
		} catch (e) {
			toast.error(e instanceof Error ? e.message : "Failed to create recipe");
		} finally {
			setSaving(false);
		}
	}
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dialog, {
		open,
		onOpenChange,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, {
			className: "max-h-[90vh] max-w-3xl overflow-y-auto",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogHeader, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle, { children: "New Recipe" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogDescription, { children: "Define a training strategy bound to a taxonomy." })] }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-4",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "grid grid-cols-2 gap-4",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Name" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
									value: name,
									onChange: (e) => setName(e.target.value)
								})]
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Taxonomy" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TaxonomyPicker, {
									value: taxonomyId,
									onChange: setTaxonomyId
								})]
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Description" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Textarea, {
								value: description,
								onChange: (e) => setDescription(e.target.value)
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "grid grid-cols-2 gap-4",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Base strategy" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
									value: baseStrategy,
									onValueChange: (v) => setBaseStrategy(v),
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectContent, { children: [
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
											value: "native_coco",
											children: "Native COCO"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
											value: "from_checkpoint",
											children: "From checkpoint"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
											value: "from_previous_step",
											children: "From previous step"
										})
									] })]
								})]
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Base checkpoint" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CheckpointPicker, {
									value: baseCheckpointId,
									onChange: setBaseCheckpointId
								})]
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "grid grid-cols-3 gap-4",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Freeze mode" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
									value: freezeMode,
									onValueChange: (v) => setFreezeMode(v),
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectContent, { children: [
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
											value: "none",
											children: "None"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
											value: "freeze_n",
											children: "Freeze N layers"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
											value: "head_only",
											children: "Head only"
										})
									] })]
								})]
							}), freezeMode !== "none" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Freeze layers" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
									type: "number",
									value: freezeLayers ?? "",
									onChange: (e) => setFreezeLayers(e.target.value ? Number(e.target.value) : null)
								})]
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "grid grid-cols-3 gap-4",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "LR mode" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
									value: lrMode,
									onValueChange: (v) => setLrMode(v),
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectContent, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
										value: "uniform",
										children: "Uniform"
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
										value: "differential",
										children: "Differential"
									})] })]
								})]
							}), lrMode === "differential" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Split layer idx" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
									type: "number",
									value: splitLayerIdx ?? "",
									onChange: (e) => setSplitLayerIdx(e.target.value ? Number(e.target.value) : null)
								})]
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Backbone LR mult" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
									type: "number",
									step: "0.01",
									value: backboneLrMult ?? "",
									onChange: (e) => setBackboneLrMult(e.target.value ? Number(e.target.value) : null)
								})]
							})] })]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "grid grid-cols-4 gap-4",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Loss type" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
									value: lossType,
									onValueChange: (v) => setLossType(v),
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, {}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectContent, { children: [
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
											value: "bce",
											children: "BCE"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
											value: "focal",
											children: "Focal"
										}),
										/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
											value: "ce",
											children: "CE"
										})
									] })]
								})]
							}), lossType === "focal" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-2",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "γ (gamma)" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										type: "number",
										step: "0.1",
										value: flGamma,
										onChange: (e) => setFlGamma(Number(e.target.value))
									})]
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-2",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "α (alpha)" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										type: "number",
										step: "0.05",
										value: flAlpha,
										onChange: (e) => setFlAlpha(Number(e.target.value))
									})]
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-2",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Scale" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										type: "number",
										step: "0.1",
										value: flScale,
										onChange: (e) => setFlScale(Number(e.target.value))
									})]
								})
							] })]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "grid grid-cols-4 gap-4",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-2",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "imgsz" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										type: "number",
										value: imgsz,
										onChange: (e) => setImgsz(Number(e.target.value))
									})]
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-2",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Batch size" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										type: "number",
										value: batchSize,
										onChange: (e) => setBatchSize(Number(e.target.value))
									})]
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-2",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Epochs" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										type: "number",
										value: epochs,
										onChange: (e) => setEpochs(Number(e.target.value))
									})]
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-2",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Optimizer" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										value: optimizer,
										onChange: (e) => setOptimizer(e.target.value)
									})]
								})
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "grid grid-cols-3 gap-4",
							children: [
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-2",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "lr0" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										type: "number",
										step: "0.0001",
										value: lr0,
										onChange: (e) => setLr0(Number(e.target.value))
									})]
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-2",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "lrf" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										type: "number",
										step: "0.001",
										value: lrf,
										onChange: (e) => setLrf(Number(e.target.value))
									})]
								}),
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
									className: "space-y-2",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, { children: "Patience" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Input, {
										type: "number",
										value: patience,
										onChange: (e) => setPatience(Number(e.target.value))
									})]
								})
							]
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogFooter, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "outline",
					onClick: () => onOpenChange(false),
					children: "Cancel"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					onClick: handleSave,
					disabled: saving,
					children: saving ? "Saving..." : "Create Recipe"
				})] })
			]
		})
	});
}
function RecipeList() {
	const [recipes, setRecipes] = (0, import_react.useState)([]);
	const [loading, setLoading] = (0, import_react.useState)(true);
	const load = () => {
		setLoading(true);
		listRecipes().then((res) => setRecipes(res.recipes)).catch(() => setRecipes([])).finally(() => setLoading(false));
	};
	(0, import_react.useEffect)(() => {
		load();
	}, []);
	const [deleteId, setDeleteId] = (0, import_react.useState)(null);
	function handleDelete(id, isPreset) {
		if (isPreset) {
			toast.error("Presets are immutable");
			return;
		}
		setDeleteId(id);
	}
	async function confirmDelete() {
		if (!deleteId) return;
		const id = deleteId;
		setDeleteId(null);
		try {
			await deleteRecipe(id);
			toast.success("Recipe deleted");
			load();
		} catch (e) {
			toast.error(e instanceof Error ? e.message : "Failed to delete recipe");
		}
	}
	if (loading) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
		className: "text-sm text-muted-foreground",
		children: "Loading recipes..."
	});
	if (recipes.length === 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, {
		title: "No recipes yet",
		hint: "Pick a preset above to create your first recipe."
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "overflow-x-auto",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", {
			className: "w-full text-sm",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
				className: "border-b border-border text-left text-xs text-muted-foreground",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-3 py-2",
						children: "Name"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-3 py-2",
						children: "Stage"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-3 py-2",
						children: "Freeze"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-3 py-2",
						children: "LR"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-3 py-2",
						children: "Loss"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
						className: "px-3 py-2",
						children: "Epochs"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", { className: "px-3 py-2" })
				]
			}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", { children: recipes.map((r) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
				className: "border-b border-border hover:bg-muted/30",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
						className: "px-3 py-2",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex items-center gap-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "font-medium",
								children: r.name
							}), r.is_preset && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Badge, {
								variant: "secondary",
								className: "text-[10px]",
								children: "preset"
							})]
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
						className: "px-3 py-2 font-mono text-xs",
						children: r.stage
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
						className: "px-3 py-2 font-mono text-xs",
						children: r.freeze_mode
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
						className: "px-3 py-2 font-mono text-xs",
						children: r.lr_mode
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
						className: "px-3 py-2 font-mono text-xs",
						children: r.loss_type
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
						className: "px-3 py-2 font-mono text-xs",
						children: r.epochs
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
						className: "px-3 py-2 text-right",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "sm",
							disabled: r.is_preset,
							onClick: () => handleDelete(r.id, r.is_preset),
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Trash2, { className: "h-4 w-4" })
						})
					})
				]
			}, r.id)) })]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ConfirmDialog, {
			open: deleteId !== null,
			onOpenChange: (o) => {
				if (!o) setDeleteId(null);
			},
			title: "Delete recipe?",
			description: "The recipe will be permanently removed. Presets cannot be deleted.",
			confirmLabel: "Delete Recipe",
			onConfirm: confirmDelete
		})]
	});
}
function ChainRunStatus({ runId }) {
	const [status, setStatus] = (0, import_react.useState)(null);
	const [error, setError] = (0, import_react.useState)(null);
	(0, import_react.useEffect)(() => {
		let cancelled = false;
		const poll = async () => {
			try {
				const res = await getChainRunStatus(runId);
				if (!cancelled) setStatus(res);
				if (res.status === "completed" || res.status === "failed") {
					cancelled = true;
					return;
				}
			} catch (e) {
				if (!cancelled) setError(e instanceof Error ? e.message : "Failed to fetch status");
			}
			if (!cancelled) setTimeout(poll, 3e3);
		};
		poll();
		return () => {
			cancelled = true;
		};
	}, [runId]);
	if (error) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
		className: "text-xs text-destructive",
		children: error
	});
	if (!status) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
		className: "text-xs text-muted-foreground",
		children: "Loading run status..."
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "rounded-md border border-border bg-card p-4 space-y-3",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h4", {
					className: "text-sm font-semibold",
					children: "Chain Run Status"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
					className: "font-mono text-xs text-muted-foreground",
					children: status.status
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "space-y-2",
				children: status.jobs.map((job) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center gap-3 text-xs",
					children: [
						job.status === "running" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-4 w-4 animate-spin text-primary" }) : job.status === "completed" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CircleCheck, { className: "h-4 w-4 text-status-pass" }) : job.status === "failed" || job.status === "cancelled" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CircleX, { className: "h-4 w-4 text-status-fail" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "h-4 w-4 rounded-full border border-muted-foreground/50" }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "font-mono",
							children: ["Step ", job.step_index]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "text-muted-foreground",
							children: [
								"Job: ",
								job.job_id.slice(0, 8),
								"..."
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "ml-auto font-medium",
							children: job.status
						})
					]
				}, job.job_id))
			}),
			status.error && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
				className: "text-xs text-status-fail",
				children: ["Error: ", status.error]
			})
		]
	});
}
function ChainList() {
	const [chains, setChains] = (0, import_react.useState)([]);
	const [loading, setLoading] = (0, import_react.useState)(true);
	const [runningChainId, setRunningChainId] = (0, import_react.useState)(null);
	const [activeRunId, setActiveRunId] = (0, import_react.useState)(null);
	(0, import_react.useEffect)(() => {
		listChains().then((res) => setChains(res.chains)).catch(() => setChains([])).finally(() => setLoading(false));
	}, []);
	const handleRun = async (chainId) => {
		setRunningChainId(chainId);
		try {
			setActiveRunId((await startChainRun(chainId)).run_id);
			toast.success("Chain run started");
		} catch (e) {
			toast.error(e instanceof Error ? e.message : "Failed to start chain");
		} finally {
			setRunningChainId(null);
		}
	};
	if (loading) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
		className: "text-sm text-muted-foreground",
		children: "Loading chains..."
	});
	if (chains.length === 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, { title: "No chains defined yet" });
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-6",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "overflow-x-auto",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", {
				className: "w-full text-sm",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
					className: "border-b border-border text-left text-xs text-muted-foreground",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-3 py-2",
							children: "Name"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-3 py-2",
							children: "Stage"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-3 py-2",
							children: "Steps"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-3 py-2",
							children: "Created"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", { className: "px-3 py-2" })
					]
				}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", { children: chains.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
					className: "border-b border-border hover:bg-muted/30",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-2 font-medium",
							children: c.name
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-2 font-mono text-xs",
							children: c.stage
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-2 font-mono text-xs",
							children: c.steps.length
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-2 text-xs text-muted-foreground",
							children: new Date(c.created_at).toLocaleDateString()
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-3 py-2 text-right",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
								size: "sm",
								variant: "outline",
								disabled: runningChainId === c.id,
								onClick: () => handleRun(c.id),
								children: [runningChainId === c.id ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-4 w-4 animate-spin" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Play, { className: "h-4 w-4" }), "Run"]
							})
						})
					]
				}, c.id)) })]
			})
		}), activeRunId && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ChainRunStatus, { runId: activeRunId })]
	});
}
function TrainingDashboard() {
	const [jobs, setJobs] = (0, import_react.useState)([]);
	const [loading, setLoading] = (0, import_react.useState)(true);
	const [selectedJobId, setSelectedJobId] = (0, import_react.useState)(null);
	const [showLaunchDialog, setShowLaunchDialog] = (0, import_react.useState)(false);
	const [showRecipeBuilder, setShowRecipeBuilder] = (0, import_react.useState)(false);
	const [selectedPreset, setSelectedPreset] = (0, import_react.useState)(void 0);
	const [recipesRefreshKey, setRecipesRefreshKey] = (0, import_react.useState)(0);
	const loadJobs = async () => {
		try {
			setLoading(true);
			setJobs((await fetchTrainingJobs()).jobs);
		} catch (err) {
			console.error("Failed to load jobs", err);
		} finally {
			setLoading(false);
		}
	};
	(0, import_react.useEffect)(() => {
		loadJobs();
		const interval = setInterval(loadJobs, 5e3);
		return () => clearInterval(interval);
	}, []);
	const [stopJobId, setStopJobId] = (0, import_react.useState)(null);
	const handleStopJob = (jobId) => setStopJobId(jobId);
	const confirmStopJob = async () => {
		if (!stopJobId) return;
		const id = stopJobId;
		setStopJobId(null);
		try {
			await stopTrainingJob(id);
			toast.success("Job stop requested");
			loadJobs();
		} catch (e) {
			toast.error(e instanceof Error ? e.message : "Failed to stop job");
		}
	};
	const handlePresetSelect = (preset) => {
		setSelectedPreset(preset);
		setShowRecipeBuilder(true);
	};
	const handleRecipeSaved = () => {
		setSelectedPreset(void 0);
		setRecipesRefreshKey((k) => k + 1);
	};
	if (selectedJobId) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageShell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(JobDetailPanel, {
		jobId: selectedJobId,
		onBack: () => setSelectedJobId(null)
	}) });
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(PageShell, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
		title: "Training & Experiments",
		subtitle: "Launch training jobs, manage recipes, and monitor progress."
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Tabs, {
		defaultValue: "jobs",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsList, { children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
					value: "jobs",
					children: "Jobs"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
					value: "recipes",
					children: "Recipes"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsTrigger, {
					value: "chains",
					children: "Chains"
				})
			] }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsContent, {
				value: "jobs",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "flex items-center justify-end",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
							size: "sm",
							onClick: () => setShowLaunchDialog(true),
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Play, { className: "h-4 w-4 mr-1.5" }), "Launch Training"]
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(JobListTable, {
						jobs,
						loading,
						onSelectJob: (job) => setSelectedJobId(job.id),
						onStopJob: handleStopJob
					}),
					showLaunchDialog && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(LaunchTrainingDialog, {
						onClose: () => setShowLaunchDialog(false),
						onLaunched: loadJobs
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ConfirmDialog, {
						open: stopJobId !== null,
						onOpenChange: (o) => {
							if (!o) setStopJobId(null);
						},
						title: "Stop training job?",
						description: "The training process will be terminated and the job marked as cancelled.",
						confirmLabel: "Stop Job",
						onConfirm: confirmStopJob
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(TabsContent, {
				value: "recipes",
				className: "space-y-6",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "flex items-center justify-end",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
							size: "sm",
							onClick: () => setShowRecipeBuilder(true),
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Plus, { className: "h-4 w-4 mr-1.5" }), "New Recipe"]
						})
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StrategyPresetPicker, { onSelect: handlePresetSelect }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(RecipeList, {}, recipesRefreshKey),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(RecipeBuilder, {
						open: showRecipeBuilder,
						onOpenChange: setShowRecipeBuilder,
						preset: selectedPreset,
						onSaved: handleRecipeSaved
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TabsContent, {
				value: "chains",
				className: "space-y-6",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ChainList, {})
			})
		]
	})] });
}
function TrainingPage() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TrainingDashboard, {});
}
//#endregion
export { TrainingPage as component };
