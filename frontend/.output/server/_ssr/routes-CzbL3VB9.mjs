import { n as __toESM } from "../_runtime.mjs";
import { D as fetchSystemDevices, O as fetchSystemMetrics, X as runInspection, it as updateReview, nt as submitReview } from "./apiClient-ClfACpV5.mjs";
import { t as cn } from "./utils-C_uf36nf.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { j as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { t as Button } from "./button-BkEeRci-.mjs";
import { A as Download, F as Circle, G as Ban, L as CircleCheck, N as Cpu, S as HardDrive, U as Check, W as Car, Z as Activity, _ as OctagonAlert, h as Play, l as ShieldCheck, p as RefreshCw, r as Upload, t as Zap, v as LoaderCircle } from "../_libs/lucide-react.mjs";
import { a as SelectTrigger, i as SelectItem, n as Select, o as SelectValue, r as SelectContent, t as Label } from "./label-CsQhRIhI.mjs";
import { a as panelColor, i as classColor, n as DEFECT_CLASSES, r as PANEL_LABELS, t as ALL_PANELS } from "./constants-CrQ5z6ae.mjs";
import { t as Badge } from "./badge-D1Dupn2y.mjs";
import { i as Track, n as Root, r as Thumb, t as Range } from "../_libs/radix-ui__react-slider.mjs";
import { n as Thumb$1, t as Root$1 } from "../_libs/radix-ui__react-switch.mjs";
import { t as Root$2 } from "../_libs/radix-ui__react-separator.mjs";
import { a as Viewport, i as ScrollAreaThumb, n as Root$3, r as ScrollAreaScrollbar, t as Corner } from "../_libs/radix-ui__react-scroll-area.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/routes-CzbL3VB9.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var demo_vehicle_default = "/assets/demo-vehicle-QX9El2ws.jpg";
function base64ToFile(base64, filename) {
	try {
		const arr = base64.split(",");
		if (arr.length < 2) return null;
		const mime = arr[0].match(/:(.*?);/)?.[1] || "image/jpeg";
		const bstr = atob(arr[1]);
		let n = bstr.length;
		const u8arr = new Uint8Array(n);
		while (n--) u8arr[n] = bstr.charCodeAt(n);
		return new File([u8arr], filename, { type: mime });
	} catch (e) {
		console.warn("Failed to convert base64 to file:", e);
		return null;
	}
}
var STORAGE_KEY = "car_defect_inspection_state";
var initialFilters = {
	panels: /* @__PURE__ */ new Set(),
	classes: /* @__PURE__ */ new Set(),
	minConfidence: 0,
	minDsi: 0
};
var initial = {
	imageUrl: null,
	imageName: null,
	imageFile: null,
	stage: "idle",
	message: "Awaiting image.",
	payload: null,
	filters: initialFilters,
	viewStage: 2,
	enableStage1: true,
	enableStage2: true,
	enableStage3: true
};
function serializeState(state) {
	return {
		imageUrl: state.imageUrl,
		imageName: state.imageName,
		stage: state.stage,
		message: state.message,
		payload: state.payload,
		viewStage: state.viewStage,
		enableStage1: state.enableStage1,
		enableStage2: state.enableStage2,
		enableStage3: state.enableStage3,
		filters: {
			panels: Array.from(state.filters.panels),
			classes: Array.from(state.filters.classes),
			minConfidence: state.filters.minConfidence,
			minDsi: state.filters.minDsi
		}
	};
}
function reducer(state, action) {
	switch (action.type) {
		case "set_image": return {
			...state,
			imageUrl: action.url,
			imageName: action.name,
			imageFile: action.file,
			stage: "idle",
			payload: null,
			message: "Ready to inspect."
		};
		case "stage": return {
			...state,
			stage: action.stage,
			message: action.message
		};
		case "payload": return {
			...state,
			payload: action.payload
		};
		case "reset":
			localStorage.removeItem(STORAGE_KEY);
			return {
				...initial,
				filters: initialFilters
			};
		case "filters": return {
			...state,
			filters: {
				...state.filters,
				...action.patch
			}
		};
		case "view_stage": return {
			...state,
			viewStage: action.viewStage
		};
		case "stage_toggles": return {
			...state,
			...action.patch
		};
		case "hydrate": return {
			...state,
			...action.state
		};
	}
}
function useInspection(defaults) {
	const [state, dispatch] = (0, import_react.useReducer)(reducer, {
		...initial,
		imageUrl: defaults.imageUrl,
		imageName: defaults.imageName,
		message: "Demo vehicle loaded. Ready to inspect."
	});
	(0, import_react.useEffect)(() => {
		try {
			const saved = localStorage.getItem(STORAGE_KEY);
			if (saved) {
				const parsed = JSON.parse(saved);
				const hydratedFilters = {
					panels: new Set(parsed.filters?.panels || []),
					classes: new Set(parsed.filters?.classes || []),
					minConfidence: parsed.filters?.minConfidence ?? 0,
					minDsi: parsed.filters?.minDsi ?? 0
				};
				const hydratedFile = parsed.imageUrl && parsed.imageName ? base64ToFile(parsed.imageUrl, parsed.imageName) : null;
				dispatch({
					type: "hydrate",
					state: {
						imageUrl: parsed.imageUrl,
						imageName: parsed.imageName,
						imageFile: hydratedFile,
						stage: parsed.stage || "idle",
						message: parsed.message || "Restored from previous session.",
						payload: parsed.payload,
						viewStage: parsed.viewStage || 2,
						enableStage1: parsed.enableStage1 ?? true,
						enableStage2: parsed.enableStage2 ?? true,
						enableStage3: parsed.enableStage3 ?? true,
						filters: hydratedFilters
					}
				});
			}
		} catch (e) {
			console.warn("Failed to hydrate inspection state:", e);
		}
	}, []);
	(0, import_react.useEffect)(() => {
		try {
			if (state.imageUrl === defaults.imageUrl && !state.payload) return;
			localStorage.setItem(STORAGE_KEY, JSON.stringify(serializeState(state)));
		} catch (e) {
			if (e instanceof DOMException && e.name === "QuotaExceededError") {
				console.warn("localStorage quota exceeded. Saving state without image data.");
				const stateWithoutImage = serializeState(state);
				stateWithoutImage.imageUrl = null;
				stateWithoutImage.imageName = null;
				try {
					localStorage.setItem(STORAGE_KEY, JSON.stringify(stateWithoutImage));
				} catch (e2) {
					console.warn("Failed to save inspection state even without image:", e2);
				}
			} else console.warn("Failed to save inspection state:", e);
		}
	}, [state, defaults.imageUrl]);
	const setImage = (0, import_react.useCallback)((url, name, file) => {
		if (file) {
			const reader = new FileReader();
			reader.onload = (e) => {
				const base64Url = e.target?.result;
				dispatch({
					type: "set_image",
					url: base64Url,
					name,
					file
				});
			};
			reader.readAsDataURL(file);
		} else dispatch({
			type: "set_image",
			url,
			name,
			file: null
		});
	}, []);
	const run = (0, import_react.useCallback)(async (opts) => {
		dispatch({
			type: "stage",
			stage: "processing",
			message: "Running inspection pipeline..."
		});
		dispatch({
			type: "payload",
			payload: null
		});
		if (!state.imageFile) {
			dispatch({
				type: "stage",
				stage: "error",
				message: "No image file available. Please upload an image."
			});
			return;
		}
		try {
			dispatch({
				type: "payload",
				payload: await runInspection({
					file: state.imageFile,
					modelName: opts?.modelName,
					stage2ModelName: opts?.stage2ModelName,
					stage2Mode: opts?.stage2Mode,
					stage2Preset: opts?.stage2Preset,
					stage2Conf: opts?.stage2Conf,
					device: opts?.device,
					enableStage1: state.enableStage1,
					enableStage2: state.enableStage2,
					enableStage3: state.enableStage3
				})
			});
			dispatch({
				type: "stage",
				stage: "done",
				message: "Inspection complete."
			});
		} catch (err) {
			console.error("Inspection failed:", err);
			dispatch({
				type: "stage",
				stage: "error",
				message: err instanceof Error ? err.message : "Inspection failed."
			});
		}
	}, [
		state.imageFile,
		state.enableStage1,
		state.enableStage2,
		state.enableStage3
	]);
	const reset = (0, import_react.useCallback)(() => dispatch({ type: "reset" }), []);
	const setFilters = (0, import_react.useCallback)((patch) => dispatch({
		type: "filters",
		patch
	}), []);
	const setViewStage = (0, import_react.useCallback)((viewStage) => dispatch({
		type: "view_stage",
		viewStage
	}), []);
	const setStageToggles = (0, import_react.useCallback)((patch) => dispatch({
		type: "stage_toggles",
		patch
	}), []);
	return {
		state,
		filteredDefects: (0, import_react.useMemo)(() => {
			if (!state.payload) return [];
			const { panels, classes, minConfidence, minDsi } = state.filters;
			return state.payload.defects.filter((d) => {
				if (panels.size && !panels.has(d.panel)) return false;
				if (classes.size && !classes.has(d.class)) return false;
				if (d.confidence < minConfidence) return false;
				if (d.dsi != null && d.dsi < minDsi) return false;
				return true;
			});
		}, [state.payload, state.filters]),
		setImage,
		run,
		reset,
		setFilters,
		setViewStage,
		setStageToggles
	};
}
var Slider = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Root, {
	ref,
	className: cn("relative flex w-full touch-none select-none items-center", className),
	...props,
	children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Track, {
		className: "relative h-1.5 w-full grow overflow-hidden rounded-full bg-primary/20",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Range, { className: "absolute h-full bg-primary" })
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Thumb, { className: "block h-4 w-4 rounded-full border border-primary/50 bg-background shadow transition-colors focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50" })]
}));
Slider.displayName = Root.displayName;
var Switch = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Root$1, {
	className: cn("peer inline-flex h-5 w-9 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent shadow-sm transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background disabled:cursor-not-allowed disabled:opacity-50 data-[state=checked]:bg-primary data-[state=unchecked]:bg-input", className),
	...props,
	ref,
	children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Thumb$1, { className: cn("pointer-events-none block h-4 w-4 rounded-full bg-background shadow-lg ring-0 transition-transform data-[state=checked]:translate-x-4 data-[state=unchecked]:translate-x-0") })
}));
Switch.displayName = Root$1.displayName;
var Separator = import_react.forwardRef(({ className, orientation = "horizontal", decorative = true, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Root$2, {
	ref,
	decorative,
	orientation,
	className: cn("shrink-0 bg-border", orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]", className),
	...props
}));
Separator.displayName = Root$2.displayName;
function SystemMetricsPanel() {
	const [metrics, setMetrics] = (0, import_react.useState)(null);
	(0, import_react.useEffect)(() => {
		let active = true;
		const poll = async () => {
			try {
				const data = await fetchSystemMetrics();
				if (active) setMetrics(data);
			} catch (e) {}
		};
		poll();
		const id = setInterval(poll, 2e3);
		return () => {
			active = false;
			clearInterval(id);
		};
	}, []);
	if (!metrics) return null;
	const ramPercent = metrics.ram_total_gb > 0 ? Math.min(100, metrics.ram_used_gb / metrics.ram_total_gb * 100) : 0;
	const gpuMemPercent = metrics.gpu_name !== null && metrics.gpu_vram_total_gb ? Math.min(100, (metrics.gpu_vram_used_gb ?? 0) / metrics.gpu_vram_total_gb * 100) : 0;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-2 rounded-sm border border-border bg-card/40 p-3",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground",
				children: "System Telemetry"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center justify-between text-[10px]",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
						className: "flex items-center gap-1 font-mono uppercase text-muted-foreground",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Cpu, { className: "h-3 w-3" }), " CPU"]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
						className: "font-mono",
						children: [metrics.cpu_percent.toFixed(0), "%"]
					})]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "h-1.5 w-full overflow-hidden rounded-full bg-muted",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "h-full bg-primary transition-all",
						style: { width: `${metrics.cpu_percent}%` }
					})
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center justify-between text-[10px]",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
						className: "flex items-center gap-1 font-mono uppercase text-muted-foreground",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(HardDrive, { className: "h-3 w-3" }), " RAM"]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
						className: "font-mono",
						children: [
							metrics.ram_used_gb,
							" / ",
							metrics.ram_total_gb,
							" GB"
						]
					})]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "h-1.5 w-full overflow-hidden rounded-full bg-muted",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "h-full bg-primary transition-all",
						style: { width: `${ramPercent}%` }
					})
				})]
			}),
			metrics.gpu_name !== null ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center justify-between text-[10px]",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "flex min-w-0 items-center gap-1 font-mono uppercase text-muted-foreground",
							title: metrics.gpu_name,
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Zap, { className: "h-3 w-3 shrink-0" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "truncate",
								children: metrics.gpu_name
							})]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "shrink-0 font-mono",
							children: [
								metrics.gpu_vram_used_gb ?? 0,
								" / ",
								metrics.gpu_vram_total_gb ?? 0,
								" GB"
							]
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "h-1.5 w-full overflow-hidden rounded-full bg-muted",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "h-full bg-primary transition-all",
							style: { width: `${gpuMemPercent}%` }
						})
					}),
					metrics.gpu_utilization_percent !== null && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
						className: "text-right font-mono text-[10px] text-muted-foreground",
						children: [metrics.gpu_utilization_percent.toFixed(0), "% UTIL"]
					})
				]
			}) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center gap-1 font-mono text-[10px] uppercase text-muted-foreground/60",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Zap, { className: "h-3 w-3" }), " No GPU detected"]
			})
		]
	});
}
var STAGES = [
	{
		key: "prescreen",
		stageId: "stage1",
		label: "Stage 1 · Binary Pre-Screen (SOD)"
	},
	{
		key: "tiling",
		stageId: "stage2",
		label: "Stage 2 · Tiled Instance Segmentation"
	},
	{
		key: "context",
		stageId: "stage3",
		label: "Stage 3 · Component Context Mapping"
	}
];
var order = [
	"idle",
	"prescreen",
	"tiling",
	"context",
	"done"
];
function StageStatus({ stage, disabledStages }) {
	const currentIdx = order.indexOf(stage);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("ol", {
		className: "space-y-2",
		children: STAGES.map((s) => {
			const disabled = disabledStages?.includes(s.stageId) ?? false;
			const idx = order.indexOf(s.key);
			const done = !disabled && (currentIdx > idx || stage === "done");
			const active = !disabled && stage === s.key;
			return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", {
				className: cn("flex items-start gap-3 rounded-md border border-border/60 px-3 py-2 text-xs", active && "border-primary/60 bg-primary/5", done && "text-muted-foreground", disabled && "border-border/40 text-muted-foreground/60"),
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "mt-0.5",
						children: disabled ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Ban, { className: "h-3.5 w-3.5 text-muted-foreground/50" }) : done ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Check, { className: "h-3.5 w-3.5 text-status-pass" }) : active ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-3.5 w-3.5 animate-spin text-primary" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Circle, { className: "h-3.5 w-3.5 text-muted-foreground/50" })
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "leading-snug",
						children: s.label
					}),
					disabled && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "ml-auto shrink-0 rounded-sm border border-border/60 bg-muted/40 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-muted-foreground/70",
						children: "Disabled"
					})
				]
			}, s.key);
		})
	});
}
var VIEW_STAGES = [
	{
		id: 1,
		label: "Pre-Screen"
	},
	{
		id: 2,
		label: "Defects"
	},
	{
		id: 3,
		label: "Context"
	}
];
function ControlSidebar({ imageName, stage, message, payload, filters, viewStage = 2, onImage, onRun, onReset, onFilters, onViewStage, enableStage1, enableStage2, enableStage3, onStageToggles }) {
	const inputRef = (0, import_react.useRef)(null);
	const [models, setModels] = (0, import_react.useState)([]);
	const [selectedModel, setSelectedModel] = (0, import_react.useState)("");
	const [selectedStage2Model, setSelectedStage2Model] = (0, import_react.useState)("");
	const [stage2Mode, setStage2Mode] = (0, import_react.useState)("direct");
	const [stage2Preset, setStage2Preset] = (0, import_react.useState)("balanced");
	const [stage2Conf, setStage2Conf] = (0, import_react.useState)(.15);
	const [devices, setDevices] = (0, import_react.useState)(null);
	const [device, setDevice] = (0, import_react.useState)("auto");
	const [stage2Models, setStage2Models] = (0, import_react.useState)([]);
	const [stage3Models, setStage3Models] = (0, import_react.useState)([]);
	const [selectedStage3Model, setSelectedStage3Model] = (0, import_react.useState)("");
	(0, import_react.useEffect)(() => {
		fetch("http://localhost:8010/api/models").then((res) => res.json()).then((data) => {
			const s1 = data.models || data.stage1 || [];
			setModels(s1);
			if (s1.length > 0) setSelectedModel(s1[0]);
			const s2 = data.stage2 || [];
			setStage2Models(s2);
			if (s2.length > 0) setSelectedStage2Model(s2[0]);
			const s3 = data.stage3 || [];
			setStage3Models(s3);
			if (s3.length > 0) setSelectedStage3Model(s3[0]);
		}).catch((err) => console.error("Failed to fetch models:", err));
		fetchSystemDevices().then(setDevices).catch((err) => console.error("Failed to fetch devices:", err));
	}, []);
	const handleFile = (e) => {
		const f = e.target.files?.[0];
		if (f) onImage(f);
	};
	const handleDrop = (e) => {
		e.preventDefault();
		const f = e.dataTransfer.files?.[0];
		if (f && f.type.startsWith("image/")) onImage(f);
	};
	const togglePanel = (id) => {
		const next = new Set(filters.panels);
		if (next.has(id)) next.delete(id);
		else next.add(id);
		onFilters({ panels: next });
	};
	const toggleClass = (id) => {
		const next = new Set(filters.classes);
		if (next.has(id)) next.delete(id);
		else next.add(id);
		onFilters({ classes: next });
	};
	const exportJson = () => {
		if (!payload) return;
		const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = `inspection-${payload.timestamp}.json`;
		a.click();
		URL.revokeObjectURL(url);
	};
	const running = stage !== "idle" && stage !== "done";
	const allStagesOff = !enableStage1 && !enableStage2 && !enableStage3;
	const disabledStages = payload?.disabled_stages ?? [
		...enableStage1 ? [] : ["stage1"],
		...enableStage2 ? [] : ["stage2"],
		...enableStage3 ? [] : ["stage3"]
	];
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("aside", {
		className: "flex h-full flex-col gap-5 overflow-y-auto border-r border-border bg-sidebar/40 p-5",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground",
				children: "Zone A · Controls"
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
				className: "mt-1 text-sm font-semibold uppercase tracking-wide",
				children: "Inspection Console"
			})] }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				onDrop: handleDrop,
				onDragOver: (e) => e.preventDefault(),
				className: "rounded-sm border border-dashed border-border bg-card/40 p-4 text-center",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Upload, { className: "mx-auto h-5 w-5 text-muted-foreground" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "mt-2 text-xs text-muted-foreground",
						children: "Drop a high-res vehicle frame or"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "ghost",
						size: "sm",
						className: "mt-1 h-7 text-xs",
						onClick: () => inputRef.current?.click(),
						children: "Browse image"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
						ref: inputRef,
						type: "file",
						accept: "image/*",
						className: "hidden",
						onChange: handleFile
					}),
					imageName && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "mt-2 truncate text-[11px] text-foreground/70",
						children: imageName
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1.5",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground",
					children: "Stage 1 Model"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
					value: selectedModel,
					onValueChange: setSelectedModel,
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
						className: "h-8 text-xs",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, { placeholder: "Select a model" })
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectContent, { children: models.map((m) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
						value: m,
						className: "text-xs",
						children: m
					}, m)) })]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1.5",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground",
					children: "Stage 2 Model"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
					value: selectedStage2Model,
					onValueChange: setSelectedStage2Model,
					disabled: stage2Models.length === 0,
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
						className: "h-8 text-xs",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, { placeholder: stage2Models.length === 0 ? "No Stage 2 models" : "Select a model" })
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectContent, { children: stage2Models.map((m) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
						value: m,
						className: "text-xs",
						children: m
					}, m)) })]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1.5",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground",
					children: "Stage 2 Inference"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "grid grid-cols-2 gap-1 rounded-sm border border-border bg-card/40 p-1",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						type: "button",
						onClick: () => setStage2Mode("direct"),
						className: cn("rounded-sm px-1 py-1.5 text-center text-[10px] font-medium uppercase tracking-wide transition", stage2Mode === "direct" ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:bg-accent hover:text-foreground"),
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "block font-mono text-[9px] uppercase tracking-wider opacity-70",
							children: "Fast"
						})
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						type: "button",
						onClick: () => setStage2Mode("sahi"),
						className: cn("rounded-sm px-1 py-1.5 text-center text-[10px] font-medium uppercase tracking-wide transition", stage2Mode === "sahi" ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:bg-accent hover:text-foreground"),
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "block font-mono text-[9px] uppercase tracking-wider opacity-70",
							children: "High-recall"
						})
					})]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1.5",
				title: "Presets apply to the SAHI pipeline",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground",
						children: "SAHI Preset"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
						value: stage2Preset,
						onValueChange: (v) => setStage2Preset(v),
						disabled: stage2Mode !== "sahi",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
							className: "h-8 text-xs",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, { placeholder: "Select preset" })
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectContent, { children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
								value: "balanced",
								className: "text-xs",
								children: "Balanced"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
								value: "safety",
								className: "text-xs",
								children: "Safety"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
								value: "max_recall",
								className: "text-xs",
								children: "Max Recall"
							})
						] })]
					}),
					stage2Mode !== "sahi" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-[10px] text-muted-foreground",
						children: "Presets apply to the SAHI pipeline."
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1.5",
				title: "Direct confidence applies to Fast mode only",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "mb-1 flex items-center justify-between",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "font-mono text-[11px] font-medium uppercase tracking-wide",
							children: "Direct Confidence"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Badge, {
							variant: "secondary",
							className: "h-5 text-[10px]",
							children: [Math.round(stage2Conf * 100), "%"]
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Slider, {
						value: [stage2Conf * 100],
						min: 5,
						max: 50,
						step: 1,
						disabled: stage2Mode !== "direct",
						onValueChange: (v) => setStage2Conf(v[0] / 100)
					}),
					stage2Mode !== "direct" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-[10px] text-muted-foreground",
						children: "Direct confidence applies to Fast mode only."
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1.5",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground",
					children: "Stage 3 Model"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
					value: selectedStage3Model,
					onValueChange: setSelectedStage3Model,
					disabled: stage3Models.length === 0,
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
						className: "h-8 text-xs",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, { placeholder: stage3Models.length === 0 ? "No Stage 3 models" : "Select a model" })
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectContent, { children: stage3Models.map((m) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
						value: m,
						className: "text-xs",
						children: m
					}, m)) })]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1.5",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground",
					children: "Compute Device"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
					value: device,
					onValueChange: setDevice,
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, {
						className: "h-8 text-xs",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, { placeholder: "Select device" })
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectContent, { children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
							value: "auto",
							className: "text-xs",
							children: "Auto (Best Available)"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
							value: "cpu",
							className: "text-xs",
							children: "CPU"
						}),
						devices?.mps && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
							value: "mps",
							className: "text-xs",
							children: "MPS (Apple Silicon)"
						}),
						devices?.cuda && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectItem, {
							value: "cuda:0",
							className: "text-xs",
							children: [
								"CUDA (",
								devices.cuda_name || "GPU",
								")"
							]
						})
					] })]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1.5",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground",
					children: "Pipeline stages"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-3 rounded-sm border border-border bg-card/40 p-3",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex items-center justify-between gap-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-0.5",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
									htmlFor: "toggle-stage1",
									className: "text-[11px] font-medium",
									children: "Stage 1 — Anomaly screener"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-[10px] leading-snug text-muted-foreground",
									children: "Pre-screen; skips heavy processing on clean vehicles."
								})]
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Switch, {
								id: "toggle-stage1",
								checked: enableStage1,
								onCheckedChange: (v) => onStageToggles({ enableStage1: v })
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex items-center justify-between gap-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-0.5",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
									htmlFor: "toggle-stage2",
									className: "text-[11px] font-medium",
									children: "Stage 2 — Defect classes"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-[10px] leading-snug text-muted-foreground",
									children: "Detects and classifies defects on image tiles."
								})]
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Switch, {
								id: "toggle-stage2",
								checked: enableStage2,
								onCheckedChange: (v) => onStageToggles({ enableStage2: v })
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex items-center justify-between gap-3",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-0.5",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Label, {
									htmlFor: "toggle-stage3",
									className: "text-[11px] font-medium",
									children: "Stage 3 — Panel context"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-[10px] leading-snug text-muted-foreground",
									children: "Maps detections to vehicle panels for context."
								})]
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Switch, {
								id: "toggle-stage3",
								checked: enableStage3,
								onCheckedChange: (v) => onStageToggles({ enableStage3: v })
							})]
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-2",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
						className: "w-full rounded-sm uppercase tracking-wide",
						onClick: () => onRun({
							modelName: selectedModel,
							stage2ModelName: selectedStage2Model || void 0,
							stage2Mode,
							stage2Preset: stage2Mode === "sahi" ? stage2Preset : void 0,
							stage2Conf: stage2Mode === "direct" ? stage2Conf : void 0,
							device
						}),
						disabled: running || allStagesOff,
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Play, { className: "mr-2 h-4 w-4" }), "Run Inspection"]
					}),
					allStagesOff && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-[10px] text-muted-foreground",
						children: "Enable at least one stage"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid grid-cols-2 gap-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
							variant: "outline",
							size: "sm",
							className: "rounded-sm",
							onClick: () => onRun({ forceClean: true }),
							disabled: running,
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ShieldCheck, { className: "mr-1.5 h-3.5 w-3.5" }), "Simulate clean"]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
							variant: "outline",
							size: "sm",
							className: "rounded-sm",
							onClick: onReset,
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(RefreshCw, { className: "mr-1.5 h-3.5 w-3.5" }), "Reset"]
						})]
					})
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(StageStatus, {
					stage,
					disabledStages
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-[11px] leading-snug text-muted-foreground",
					children: message
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-1.5",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-[11px] font-medium uppercase tracking-wider text-muted-foreground",
					children: "Stage layer view"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "grid grid-cols-3 gap-1 rounded-sm border border-border bg-card/40 p-1",
					children: VIEW_STAGES.map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
						onClick: () => onViewStage?.(s.id),
						className: cn("rounded-sm px-1 py-1.5 text-center text-[10px] font-medium uppercase tracking-wide transition", viewStage === s.id ? "bg-primary text-primary-foreground shadow-sm" : "text-muted-foreground hover:bg-accent hover:text-foreground"),
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "block font-mono text-[9px] uppercase tracking-wider opacity-70",
							children: ["S", s.id]
						}), s.label]
					}, s.id))
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Separator, {}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
				className: "space-y-3",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
						className: "text-xs font-semibold uppercase tracking-wider text-muted-foreground",
						children: "Filters"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "mb-1.5 text-[11px] font-medium",
						children: "Panels"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "flex flex-wrap gap-1",
						children: ALL_PANELS.map((p) => {
							return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
								onClick: () => togglePanel(p),
								className: cn("rounded-sm border px-2 py-0.5 font-mono text-[10px] uppercase transition", filters.panels.has(p) ? "border-primary bg-primary text-primary-foreground" : "border-border text-muted-foreground hover:bg-accent"),
								children: PANEL_LABELS[p]
							}, p);
						})
					})] }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "mb-1.5 text-[11px] font-medium",
						children: "Defect classes"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "flex flex-wrap gap-1",
						children: DEFECT_CLASSES.map((c) => {
							return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
								onClick: () => toggleClass(c.id),
								className: cn("flex items-center gap-1 rounded-sm border px-2 py-0.5 font-mono text-[10px] uppercase transition", filters.classes.has(c.id) ? "border-foreground/60 bg-foreground/10" : "border-border text-muted-foreground hover:bg-accent"),
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "h-2 w-2 rounded-full",
									style: { backgroundColor: c.color }
								}), c.label]
							}, c.id);
						})
					})] }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "mb-1 flex items-center justify-between",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "font-mono text-[11px] font-medium uppercase tracking-wide",
							children: "Min confidence"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Badge, {
							variant: "secondary",
							className: "h-5 text-[10px]",
							children: [Math.round(filters.minConfidence * 100), "%"]
						})]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Slider, {
						value: [filters.minConfidence * 100],
						max: 100,
						step: 1,
						onValueChange: (v) => onFilters({ minConfidence: v[0] / 100 })
					})] }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "mb-1 flex items-center justify-between",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "font-mono text-[11px] font-medium uppercase tracking-wide",
							children: "Min DSI"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Badge, {
							variant: "secondary",
							className: "h-5 text-[10px]",
							children: [(filters.minDsi * 100).toFixed(2), "%"]
						})]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Slider, {
						value: [filters.minDsi * 1e3],
						max: 20,
						step: .1,
						onValueChange: (v) => onFilters({ minDsi: v[0] / 1e3 })
					})] })
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Separator, {}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
				variant: "outline",
				size: "sm",
				className: "rounded-sm font-mono uppercase tracking-wide",
				onClick: exportJson,
				disabled: !payload,
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Download, { className: "mr-1.5 h-3.5 w-3.5" }), "Export JSON"]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SystemMetricsPanel, {})
		]
	});
}
function toPoints(polygon, w, h) {
	return polygon.map(([x, y]) => `${x * w},${y * h}`).join(" ");
}
function defectMatchesViewStage(d, viewStage) {
	const isAnomaly = d.class === "anomaly";
	if (viewStage === 1) return isAnomaly;
	return !isAnomaly;
}
function InspectionCanvas({ imageUrl, payload, visibleDefects, hoveredId, onHover, viewStage = 2 }) {
	const { W, H } = (0, import_react.useMemo)(() => {
		const dims = payload?.imageDims;
		return {
			W: dims?.width ?? 1600,
			H: dims?.height ?? 900
		};
	}, [payload]);
	const preScreenChip = payload ? payload.preScreen?.anomalyDetected ? {
		label: "Active Route",
		tone: "warn"
	} : {
		label: "Pass",
		tone: "pass"
	} : {
		label: "Awaiting run",
		tone: "idle"
	};
	const visibleIds = new Set(visibleDefects.map((d) => d.id));
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "relative flex h-full flex-col",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "flex items-center justify-between border-b border-border px-5 py-3",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground ",
				children: "Zone B · Global Spatial Context"
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
				className: "mt-0.5 text-sm font-semibold uppercase tracking-wide ",
				children: "High-resolution canvas"
			})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: cn("flex items-center gap-2 rounded-sm border px-3 py-1 font-mono text-[11px] font-medium uppercase tracking-wide ", preScreenChip.tone === "pass" && "border-status-pass/40 bg-status-pass/10 text-status-pass", preScreenChip.tone === "warn" && "border-amber-500/40 bg-amber-500/10 text-amber-600 dark:text-amber-400", preScreenChip.tone === "idle" && "border-border text-muted-foreground"),
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: cn("h-1.5 w-1.5 rounded-full", preScreenChip.tone === "pass" && "bg-status-pass", preScreenChip.tone === "warn" && "bg-amber-500 animate-pulse", preScreenChip.tone === "idle" && "bg-muted-foreground") }),
					"Pre-screen: ",
					preScreenChip.label,
					payload && payload.inspection_status === "FAIL" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
						className: "text-muted-foreground",
						children: [
							"· ",
							payload.total_defects_found,
							" defect(s)"
						]
					})
				]
			})]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "relative flex-1 overflow-hidden bg-black/10 p-4 dark:bg-black/60",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "relative mx-auto h-full w-full max-w-[1400px] rounded-sm border border-border/40",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "relative h-full w-full",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("img", {
						src: imageUrl,
						alt: "Vehicle under inspection",
						className: "absolute inset-0 h-full w-full object-contain"
					}), payload && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("svg", {
						viewBox: `0 0 ${W} ${H}`,
						className: "absolute inset-0 h-full w-full",
						preserveAspectRatio: "xMidYMid meet",
						children: [
							viewStage === 1 && Array.isArray(payload.stage1_blobs) && payload.stage1_blobs.map((b) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("g", { children: b.polygon && b.polygon.length > 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("polygon", {
								points: toPoints(b.polygon, W, H),
								fill: "var(--defect-anomaly)",
								fillOpacity: .35,
								stroke: "var(--defect-anomaly)",
								strokeWidth: 1.5
							}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("rect", {
								x: b.bbox[0] * W,
								y: b.bbox[1] * H,
								width: (b.bbox[2] - b.bbox[0]) * W,
								height: (b.bbox[3] - b.bbox[1]) * H,
								fill: "var(--defect-anomaly)",
								fillOpacity: .35,
								stroke: "var(--defect-anomaly)",
								strokeWidth: 1.5
							}) }, b.id)),
							Array.isArray(payload.panels) && payload.panels.map((p) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("polygon", {
								points: p.polygon.map(([x, y]) => `${x * W},${y * H}`).join(" "),
								fill: viewStage === 3 ? panelColor(p.label) : "none",
								fillOpacity: viewStage === 3 ? .35 : 0,
								stroke: viewStage === 3 ? panelColor(p.label) : "currentColor",
								strokeWidth: viewStage === 3 ? 2 : 1.5,
								strokeDasharray: "6 4",
								className: viewStage === 3 ? "" : "text-primary/40"
							}, p.id)),
							Array.isArray(payload.panels) && payload.panels?.map((p) => {
								if (!p.polygon || p.polygon.length === 0) return null;
								return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("text", {
									x: p.polygon.reduce((s, pt) => s + pt[0], 0) / p.polygon.length * W,
									y: p.polygon.reduce((s, pt) => s + pt[1], 0) / p.polygon.length * H,
									fontSize: 11,
									textAnchor: "middle",
									className: viewStage === 3 ? "font-mono uppercase" : "fill-primary/60 font-mono uppercase",
									style: {
										pointerEvents: "none",
										...viewStage === 3 ? { fill: panelColor(p.label) } : {}
									},
									children: p.label
								}, `t-${p.id}`);
							}),
							Array.isArray(payload.panels) && payload.panels?.map((p) => {
								if (!p.polygon || p.polygon.length === 0) return null;
								return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("text", {
									x: p.polygon.reduce((s, pt) => s + pt[0], 0) / p.polygon.length * W,
									y: p.polygon.reduce((s, pt) => s + pt[1], 0) / p.polygon.length * H,
									fontSize: 11,
									textAnchor: "middle",
									className: viewStage === 3 ? "font-mono uppercase" : "fill-primary/60 font-mono uppercase",
									style: {
										pointerEvents: "none",
										...viewStage === 3 ? { fill: panelColor(p.label) } : {}
									},
									children: p.label
								}, `t-${p.id}`);
							}),
							payload.defects.map((d) => {
								if (!defectMatchesViewStage(d, viewStage)) return null;
								const visible = visibleIds.has(d.id);
								const isHover = hoveredId === d.id;
								const color = classColor(d.class);
								const bbox = d.bbox ?? [
									0,
									0,
									0,
									0
								];
								const poly = d.polygon ?? [];
								return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("g", {
									onMouseEnter: () => onHover(d.id),
									onMouseLeave: () => onHover(null),
									style: {
										cursor: "pointer",
										opacity: visible ? 1 : .1
									},
									children: [poly.length > 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("polygon", {
										points: toPoints(poly, W, H),
										fill: color,
										fillOpacity: isHover ? .55 : .3,
										stroke: color,
										strokeWidth: isHover ? 3 : 1.5
									}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("circle", {
										cx: (bbox[0] + bbox[2]) / 2 * W,
										cy: (bbox[1] + bbox[3]) / 2 * H,
										r: isHover ? 28 : 20,
										fill: "none",
										stroke: color,
										strokeWidth: isHover ? 2 : 1,
										strokeOpacity: .7
									})]
								}, d.id);
							})
						]
					})]
				})
			})
		})]
	});
}
var ScrollArea = import_react.forwardRef(({ className, children, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Root$3, {
	ref,
	className: cn("relative overflow-hidden", className),
	...props,
	children: [
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Viewport, {
			className: "h-full w-full rounded-[inherit]",
			children
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScrollBar, {}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Corner, {})
	]
}));
ScrollArea.displayName = Root$3.displayName;
var ScrollBar = import_react.forwardRef(({ className, orientation = "vertical", ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScrollAreaScrollbar, {
	ref,
	orientation,
	className: cn("flex touch-none select-none transition-colors", orientation === "vertical" && "h-full w-2.5 border-l border-l-transparent p-[1px]", orientation === "horizontal" && "h-2.5 flex-col border-t border-t-transparent p-[1px]", className),
	...props,
	children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScrollAreaThumb, { className: "relative flex-1 rounded-full bg-border" })
}));
ScrollBar.displayName = ScrollAreaScrollbar.displayName;
/** Shared crop math for card previews (normalized bbox -> CSS background). */
function cropBox(bbox) {
	const [x1, y1, x2, y2] = bbox;
	const w = Math.max(0, x2 - x1);
	const h = Math.max(0, y2 - y1);
	const pad = .02;
	const cx = Math.max(0, x1 - pad);
	const cy = Math.max(0, y1 - pad);
	return {
		x: x1,
		y: y1,
		w,
		h,
		cx,
		cy,
		cw: Math.min(1 - cx, w + pad * 2),
		ch: Math.min(1 - cy, h + pad * 2)
	};
}
function getCropStyle(imageUrl, bbox) {
	const { cx, cy, cw, ch } = cropBox(bbox);
	return {
		backgroundImage: `url(${imageUrl})`,
		backgroundRepeat: "no-repeat",
		backgroundSize: `${100 / cw}% ${100 / ch}%`,
		backgroundPosition: `${cx / (1 - cw) * 100}% ${cy / (1 - ch) * 100}%`
	};
}
/** Shared operator feedback controls: confirm / reject / reclassify / unclear. */
function ReviewFooter({ inspectionId, predictedClass, predictedPanel, defectId }) {
	const [decision, setDecision] = (0, import_react.useState)(null);
	const [reclassifyClass, setReclassifyClass] = (0, import_react.useState)(predictedClass !== "anomaly" ? predictedClass : "scratch");
	const [submitting, setSubmitting] = (0, import_react.useState)(false);
	const [reviewed, setReviewed] = (0, import_react.useState)(null);
	const [reviewId, setReviewId] = (0, import_react.useState)(null);
	const [error, setError] = (0, import_react.useState)(null);
	const canReview = Boolean(inspectionId) && !reviewed && !submitting;
	async function sendReview(operatorDecision, correctedClass = null) {
		if (!inspectionId) return;
		setSubmitting(true);
		setError(null);
		try {
			if (reviewId) await updateReview(reviewId, {
				operator_decision: operatorDecision,
				corrected_class: correctedClass
			});
			else setReviewId((await submitReview({
				inspection_id: inspectionId,
				defect_id: defectId,
				predicted_class: predictedClass,
				predicted_panel: predictedPanel,
				operator_decision: operatorDecision,
				corrected_class: correctedClass
			})).id);
			setReviewed(operatorDecision);
			setDecision(operatorDecision);
		} catch (err) {
			setError(err instanceof Error ? err.message : "Review failed");
		} finally {
			setSubmitting(false);
		}
	}
	const btn = (color, active = false) => cn("rounded-sm border px-2 py-1 font-mono text-[9px] uppercase tracking-wider transition disabled:cursor-not-allowed disabled:opacity-40", color === "green" && "border-green-500/40 text-green-600 hover:bg-green-500/10 dark:text-green-400", color === "red" && "border-red-500/40 text-red-600 hover:bg-red-500/10 dark:text-red-400", color === "blue" && "border-blue-500/40 text-blue-600 hover:bg-blue-500/10 dark:text-blue-400", color === "yellow" && "border-yellow-500/40 text-yellow-600 hover:bg-yellow-500/10 dark:text-yellow-400", active && "bg-blue-500/10");
	if (reviewed) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex items-center justify-between gap-2",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
			className: cn("rounded-sm px-2 py-1 font-mono text-[9px] uppercase tracking-wider", reviewed === "confirm" && "bg-green-500/15 text-green-600 dark:text-green-400", reviewed === "reject" && "bg-red-500/15 text-red-600 dark:text-red-400", reviewed === "reclassify" && "bg-blue-500/15 text-blue-600 dark:text-blue-400", reviewed === "unclear" && "bg-yellow-500/15 text-yellow-600 dark:text-yellow-400"),
			children: ["Reviewed: ", reviewed]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
			type: "button",
			onClick: () => setReviewed(null),
			className: "rounded-sm border border-border px-2 py-0.5 font-mono text-[9px] uppercase text-muted-foreground transition hover:bg-accent hover:text-accent-foreground",
			title: "Change your review decision",
			children: "Change"
		})]
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-2",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex flex-wrap gap-1.5",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						type: "button",
						disabled: !canReview,
						onClick: () => void sendReview("confirm"),
						className: btn("green"),
						children: "Confirm"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						type: "button",
						disabled: !canReview,
						onClick: () => void sendReview("reject"),
						className: btn("red"),
						children: "Reject"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						type: "button",
						disabled: !canReview,
						onClick: () => setDecision(decision === "reclassify" ? null : "reclassify"),
						className: btn("blue", decision === "reclassify"),
						children: "Reclassify"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						type: "button",
						disabled: !canReview,
						onClick: () => void sendReview("unclear"),
						className: btn("yellow"),
						children: "Unclear"
					})
				]
			}),
			decision === "reclassify" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center gap-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("select", {
					value: reclassifyClass,
					onChange: (e) => setReclassifyClass(e.target.value),
					className: "h-7 flex-1 rounded-sm border border-input bg-background px-2 font-mono text-[10px]",
					children: DEFECT_CLASSES.filter((c) => c.id !== "anomaly").map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
						value: c.id,
						children: c.label
					}, c.id))
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
					type: "button",
					disabled: !canReview,
					onClick: () => void sendReview("reclassify", reclassifyClass),
					className: btn("blue"),
					children: "Save"
				})]
			}),
			error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "font-mono text-[9px] text-red-500",
				children: error
			})
		]
	});
}
function AnomalyCard({ anomaly, imageUrl, inspectionId }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "overflow-hidden rounded-sm border border-amber-500/50 bg-card",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "relative aspect-[4/3] w-full",
			style: getCropStyle(imageUrl, anomaly.bbox),
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("svg", {
					viewBox: "0 0 100 100",
					preserveAspectRatio: "none",
					className: "absolute inset-0 h-full w-full",
					children: anomaly.polygon && anomaly.polygon.length > 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("polygon", {
						points: anomaly.polygon.map(([x, y]) => `${x * 100},${y * 100}`).join(" "),
						fill: "none",
						stroke: "var(--defect-anomaly)",
						strokeWidth: 1,
						vectorEffect: "non-scaling-stroke"
					}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("rect", {
						x: anomaly.bbox[0] * 100,
						y: anomaly.bbox[1] * 100,
						width: (anomaly.bbox[2] - anomaly.bbox[0]) * 100,
						height: (anomaly.bbox[3] - anomaly.bbox[1]) * 100,
						fill: "none",
						stroke: "var(--defect-anomaly)",
						strokeWidth: 1,
						vectorEffect: "non-scaling-stroke"
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "absolute left-2 top-2 flex items-center gap-1.5 rounded-sm bg-background/90 px-2 py-0.5 font-mono text-[10px] font-medium uppercase backdrop-blur",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "h-1.5 w-1.5 rounded-full",
						style: { backgroundColor: "var(--defect-anomaly)" }
					}), "Anomaly (Rescued)"]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "absolute right-2 top-2 rounded-sm bg-background/90 px-2 py-0.5 font-mono text-[10px] font-medium backdrop-blur",
					children: [(anomaly.confidence * 100).toFixed(0), "%"]
				})
			]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "grid grid-cols-2 gap-2 p-3 text-[11px]",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "col-span-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "font-mono text-[9px] uppercase tracking-wider text-muted-foreground",
						children: "Panel"
					}), !anomaly.panel || anomaly.panel === "Unknown" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "inline-block rounded-sm border border-border bg-muted/40 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground",
						children: "Unknown panel"
					}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "font-medium",
						children: PANEL_LABELS[anomaly.panel] ?? anomaly.panel
					})]
				}),
				anomaly.low_context && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "col-span-2",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "inline-block rounded-sm border border-amber-500/40 bg-amber-500/10 px-1.5 py-0.5 font-mono text-[9px] uppercase tracking-wider text-amber-600 dark:text-amber-400",
						children: "low context"
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "col-span-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "font-mono text-[9px] uppercase tracking-wider text-muted-foreground",
						children: "Reason"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "font-mono text-amber-500",
						children: anomaly.reason
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "col-span-2 border-t border-border pt-2",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ReviewFooter, {
						inspectionId,
						predictedClass: "anomaly",
						predictedPanel: anomaly.panel,
						defectId: anomaly.id
					})
				})
			]
		})]
	});
}
function DefectCard({ defect, imageUrl, isHovered, onHover, inspectionId }) {
	const { x, y, w, h, cx, cy, cw, ch } = cropBox(defect.bbox);
	const label = DEFECT_CLASSES.find((c) => c.id === defect.class)?.label ?? defect.class;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		onMouseEnter: () => onHover(defect.id),
		onMouseLeave: () => onHover(null),
		className: cn("group overflow-hidden rounded-sm border border-border bg-card transition", isHovered && "border-primary ring-1 ring-primary"),
		"data-defect-id": defect.id,
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "relative aspect-[4/3] w-full",
			style: getCropStyle(imageUrl, defect.bbox),
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("svg", {
					viewBox: "0 0 100 100",
					preserveAspectRatio: "none",
					className: "absolute inset-0 h-full w-full",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("rect", {
						x: (x - cx) / cw * 100,
						y: (y - cy) / ch * 100,
						width: w / cw * 100,
						height: h / ch * 100,
						fill: "none",
						stroke: classColor(defect.class),
						strokeWidth: 1,
						vectorEffect: "non-scaling-stroke"
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "absolute left-2 top-2 flex items-center gap-1.5 rounded-sm bg-background/90 px-2 py-0.5 font-mono text-[10px] font-medium uppercase backdrop-blur",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "h-1.5 w-1.5 rounded-full",
						style: { backgroundColor: classColor(defect.class) }
					}), label]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "absolute right-2 top-2 rounded-sm bg-background/90 px-2 py-0.5 font-mono text-[10px] font-medium backdrop-blur",
					children: [(defect.confidence * 100).toFixed(0), "%"]
				})
			]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "grid grid-cols-3 gap-2 p-3 text-[11px]",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "col-span-3",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "font-mono text-[9px] uppercase tracking-wider text-muted-foreground",
						children: "Panel"
					}), !defect.panel || defect.panel === "Unknown" ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "inline-block rounded-sm border border-border bg-muted/40 px-1.5 py-0.5 font-mono text-[10px] text-muted-foreground",
						children: "Unknown panel"
					}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "font-medium",
						children: PANEL_LABELS[defect.panel] ?? defect.panel
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-[9px] uppercase tracking-wider text-muted-foreground",
					children: "IoD"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono",
					children: defect.iod.toFixed(3)
				})] }),
				defect.dsi != null && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-[9px] uppercase tracking-wider text-muted-foreground",
					children: "DSI"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "font-mono",
					children: [(defect.dsi * 100).toFixed(2), "%"]
				})] }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-[9px] uppercase tracking-wider text-muted-foreground",
					children: "Conf."
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "font-mono",
					children: [(defect.confidence * 100).toFixed(1), "%"]
				})] }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("details", {
					className: "col-span-3 mt-1 text-[10px] text-muted-foreground",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("summary", {
						className: "cursor-pointer",
						children: "bbox"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
						className: "font-mono",
						children: [
							"[",
							defect.bbox.map((n) => n.toFixed(3)).join(", "),
							"]"
						]
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "col-span-3 border-t border-border pt-2",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ReviewFooter, {
						inspectionId,
						predictedClass: defect.class,
						predictedPanel: defect.panel,
						defectId: defect.id
					})
				})
			]
		})]
	});
}
function SuppressedCard({ suppressed, imageUrl, inspectionId }) {
	const label = DEFECT_CLASSES.find((c) => c.id === suppressed.predicted_class)?.label ?? suppressed.predicted_class;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "overflow-hidden rounded-sm border border-border bg-card opacity-70",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "relative aspect-[4/3] w-full",
			style: getCropStyle(imageUrl, suppressed.bbox),
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("svg", {
					viewBox: "0 0 100 100",
					preserveAspectRatio: "none",
					className: "absolute inset-0 h-full w-full",
					children: suppressed.polygon && suppressed.polygon.length > 0 ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("polygon", {
						points: suppressed.polygon.map(([x, y]) => `${x * 100},${y * 100}`).join(" "),
						fill: "none",
						stroke: "var(--border)",
						strokeWidth: 1,
						strokeDasharray: "2 2",
						vectorEffect: "non-scaling-stroke"
					}) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("rect", {
						x: suppressed.bbox[0] * 100,
						y: suppressed.bbox[1] * 100,
						width: (suppressed.bbox[2] - suppressed.bbox[0]) * 100,
						height: (suppressed.bbox[3] - suppressed.bbox[1]) * 100,
						fill: "none",
						stroke: "var(--border)",
						strokeWidth: 1,
						strokeDasharray: "2 2",
						vectorEffect: "non-scaling-stroke"
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "absolute left-2 top-2 flex items-center gap-1.5 rounded-sm bg-background/90 px-2 py-0.5 font-mono text-[10px] font-medium uppercase backdrop-blur",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: "h-1.5 w-1.5 rounded-full bg-muted-foreground" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "line-through",
						children: label
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "absolute right-2 top-2 rounded-sm bg-background/90 px-2 py-0.5 font-mono text-[10px] font-medium backdrop-blur",
					children: [(suppressed.confidence * 100).toFixed(0), "%"]
				})
			]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "grid grid-cols-2 gap-2 p-3 text-[11px]",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-[9px] uppercase tracking-wider text-muted-foreground",
					children: "Panel"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-medium",
					children: PANEL_LABELS[suppressed.panel] ?? suppressed.panel
				})] }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-[9px] uppercase tracking-wider text-muted-foreground",
					children: "Reason"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-muted-foreground capitalize",
					children: suppressed.reason.replace("_", " ")
				})] }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "col-span-2 border-t border-border pt-2",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ReviewFooter, {
						inspectionId,
						predictedClass: suppressed.predicted_class,
						predictedPanel: suppressed.panel,
						defectId: suppressed.id
					})
				})
			]
		})]
	});
}
function DefectGallery({ defects, imageUrl, hoveredId, onHover, empty, inspectionId, unclassified_anomalies, suppressed_detections }) {
	const hasDefects = defects.length > 0;
	const hasAnomalies = (unclassified_anomalies?.length ?? 0) > 0;
	const hasSuppressed = (suppressed_detections?.length ?? 0) > 0;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ScrollArea, {
		className: "h-full",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "p-4",
			children: !hasDefects && !hasAnomalies && !hasSuppressed ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "rounded-sm border border-dashed border-border p-8 text-center font-mono text-xs uppercase text-muted-foreground",
				children: empty ?? "No defects match the current filters."
			}) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-6",
				children: [
					hasDefects && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h3", {
						className: "font-mono text-[10px] uppercase tracking-widest text-foreground mb-3",
						children: [
							"Classified Defects (",
							defects.length,
							")"
						]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "grid grid-cols-1 gap-3 sm:grid-cols-2",
						children: defects.map((d) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DefectCard, {
							defect: d,
							imageUrl,
							isHovered: hoveredId === d.id,
							onHover,
							inspectionId
						}, d.id))
					})] }),
					hasAnomalies && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h3", {
						className: "font-mono text-[10px] uppercase tracking-widest text-amber-500 mb-3",
						children: [
							"Rescued Anomalies (Stage 1) (",
							unclassified_anomalies.length,
							")"
						]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "grid grid-cols-1 gap-3 sm:grid-cols-2",
						children: unclassified_anomalies.map((a) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(AnomalyCard, {
							anomaly: a,
							imageUrl,
							inspectionId
						}, a.id))
					})] }),
					hasSuppressed && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h3", {
						className: "font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-3",
						children: [
							"Suppressed Detections (",
							suppressed_detections.length,
							")"
						]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "grid grid-cols-1 gap-3 sm:grid-cols-2",
						children: suppressed_detections.map((s) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SuppressedCard, {
							suppressed: s,
							imageUrl,
							inspectionId
						}, s.id))
					})] })
				]
			})
		})
	});
}
function buildReportJson(payload, options) {
	const defects = payload.defects || [];
	const anomalies = payload.unclassified_anomalies || [];
	const suppressed = payload.suppressed_detections || [];
	const panels = payload.panels || [];
	const dsiValues = defects.map((d) => d.dsi).filter((v) => v != null && v > 0);
	const maxDsi = dsiValues.length > 0 ? Math.max(...dsiValues) : 0;
	const avgDsi = dsiValues.length > 0 ? dsiValues.reduce((sum, v) => sum + v, 0) / dsiValues.length : 0;
	const countByClass = {};
	for (const d of defects) countByClass[d.class] = (countByClass[d.class] || 0) + 1;
	const panelsReport = options.includePanelPolygons ? panels.map((p) => ({
		id: p.id,
		label: p.label,
		polygon: p.polygon,
		activeArea: p.activeArea
	})) : panels.map((p) => ({
		id: p.id,
		label: p.label,
		activeArea: p.activeArea
	}));
	const report = {
		report_version: "0.1",
		generated_at: (/* @__PURE__ */ new Date()).toISOString(),
		inspection_id: payload.inspection_id,
		timestamp: payload.timestamp,
		verdict: payload.inspection_status,
		vehicle_color_detected: payload.vehicle_color_detected,
		total_defects_found: payload.total_defects_found,
		severity_summary: {
			max_dsi: Math.round(maxDsi * 100) / 100,
			avg_dsi: Math.round(avgDsi * 100) / 100,
			defect_count_by_class: countByClass
		},
		panels_detected: panels.length,
		panels: panelsReport,
		defects: defects.map((d) => ({
			id: d.id,
			class: d.class,
			confidence: d.confidence,
			panel: d.panel,
			iod: d.iod,
			dsi: d.dsi,
			bbox: d.bbox,
			polygon: d.polygon
		})),
		unclassified_anomalies: anomalies.map((a) => ({
			id: a.id,
			confidence: a.confidence,
			panel: a.panel,
			reason: a.reason,
			bbox: a.bbox
		})),
		suppressed_detections: suppressed.map((s) => ({
			id: s.id,
			predicted_class: s.predicted_class,
			confidence: s.confidence,
			panel: s.panel,
			reason: s.reason,
			bbox: s.bbox
		}))
	};
	return JSON.stringify(report, null, 2);
}
function buildReportFilename(inspectionId) {
	return `inspection_${inspectionId}_${(/* @__PURE__ */ new Date()).toISOString().replace(/[:.]/g, "-").slice(0, 19)}.json`;
}
function ExportReportButton({ payload }) {
	const [includePolygons, setIncludePolygons] = (0, import_react.useState)(false);
	const disabled = !payload;
	const handleExport = () => {
		if (!payload) return;
		const json = buildReportJson(payload, { includePanelPolygons: includePolygons });
		const blob = new Blob([json], { type: "application/json" });
		const url = URL.createObjectURL(blob);
		const a = document.createElement("a");
		a.href = url;
		a.download = buildReportFilename(payload.inspection_id);
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex items-center gap-3",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
			className: "flex items-center gap-1.5 text-xs text-muted-foreground cursor-pointer select-none",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
				type: "checkbox",
				checked: includePolygons,
				onChange: (e) => setIncludePolygons(e.target.checked),
				className: "rounded border-gray-300"
			}), "Include panel polygons"]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
			variant: "outline",
			size: "sm",
			onClick: handleExport,
			disabled,
			title: disabled ? "Run an inspection first" : "Download factory report",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Download, { className: "h-4 w-4 mr-1.5" }), "Export Report"]
		})]
	});
}
function SummaryCard({ payload, filteredCount, disabledStages }) {
	if (!payload) return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "rounded-sm border border-border bg-card p-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
			className: "font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground",
			children: "Master inspection summary"
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
			className: "mt-2 text-xs text-muted-foreground",
			children: "Run an inspection to see the report."
		})]
	});
	const fail = payload.inspection_status === "FAIL";
	const stage1Disabled = payload.preScreen == null || (disabledStages?.includes("stage1") ?? false);
	const stage3Disabled = (payload.panels?.length ?? 0) === 0 || (disabledStages?.includes("stage3") ?? false);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "rounded-sm border border-border bg-card p-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-start justify-between gap-4",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground",
					children: "Master inspection summary"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h3", {
					className: "mt-1 flex items-center gap-2 text-base font-semibold",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Car, { className: "h-4 w-4 text-muted-foreground" }), payload.vehicle_color_detected]
				})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: cn("flex items-center gap-1.5 rounded-sm px-3 py-1.5 font-mono text-sm font-bold uppercase tracking-wide", fail ? "bg-status-fail/15 text-status-fail" : "bg-status-pass/15 text-status-pass"),
					children: [fail ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(OctagonAlert, { className: "h-4 w-4" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(CircleCheck, { className: "h-4 w-4" }), payload.inspection_status]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("dl", {
				className: "mt-3 grid grid-cols-3 gap-3 text-[11px]",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dt", {
						className: "font-mono text-[9px] uppercase tracking-wider text-muted-foreground",
						children: "Pre-screen"
					}), stage1Disabled ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
						className: "font-mono text-sm",
						children: "—"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
						className: "text-[9px] text-muted-foreground/70",
						children: "Stage 1 disabled"
					})] }) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("dd", {
						className: "font-mono text-sm",
						children: [payload.preScreen?.anomalyDetected ? "Anomaly" : "Clean", payload.preScreen?.score != null && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "text-muted-foreground",
							children: [
								" ",
								"(",
								payload.preScreen.score.toFixed(2),
								")"
							]
						})]
					})] }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dt", {
						className: "font-mono text-[9px] uppercase tracking-wider text-muted-foreground",
						children: "Panels"
					}), stage3Disabled ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
						className: "font-mono text-sm",
						children: "—"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
						className: "text-[9px] text-muted-foreground/70",
						children: "Stage 3 disabled"
					})] }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
						className: "font-mono text-sm",
						children: payload.panels?.length
					})] }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dt", {
						className: "font-mono text-[9px] uppercase tracking-wider text-muted-foreground",
						children: "Defects"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("dd", {
						className: "font-mono text-sm",
						children: [filteredCount, /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "text-muted-foreground",
							children: [
								" / ",
								payload.defects.length,
								" shown"
							]
						})]
					})] }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dt", {
						className: "font-mono text-[9px] uppercase tracking-wider text-muted-foreground",
						children: "Image"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
						className: "font-mono text-sm",
						children: payload.imageDims ? `${payload.imageDims.width}×${payload.imageDims.height}` : "—"
					})] }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("dt", {
						className: "font-mono text-[9px] uppercase tracking-wider text-muted-foreground",
						children: "Time"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("dd", {
						className: "font-mono text-[10px] leading-4",
						children: new Date(payload.timestamp).toLocaleTimeString()
					})] })
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "mt-3 border-t border-border pt-3",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ExportReportButton, { payload })
			})
		]
	});
}
function InspectionDashboard() {
	const { state, filteredDefects, setImage, run, reset, setFilters, setViewStage, setStageToggles } = useInspection({
		imageUrl: demo_vehicle_default,
		imageName: "demo-vehicle.jpg"
	});
	const [hoveredId, setHoveredId] = (0, import_react.useState)(null);
	const onImage = (0, import_react.useCallback)((file) => {
		setImage(URL.createObjectURL(file), file.name, file);
	}, [setImage]);
	(0, import_react.useEffect)(() => {
		const html = document.documentElement;
		html.classList.add("dark");
		return () => html.classList.remove("dark");
	}, []);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex h-screen w-full flex-col bg-background text-foreground",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("header", {
			className: "flex items-center justify-between border-b border-border px-5 py-2.5",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center gap-3",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "grid h-8 w-8 place-items-center rounded-sm bg-primary text-primary-foreground",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Activity, { className: "h-4 w-4" })
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-[10px] font-semibold uppercase tracking-widest text-muted-foreground",
					children: "AI Farm Robotics · Line Inspection"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h1", {
					className: "text-sm font-semibold",
					children: "Component-Aware Exterior Defect Pipeline"
				})] })]
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "hidden items-center gap-4 sm:flex",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center gap-1.5 font-mono text-[10px] uppercase tracking-wider text-muted-foreground",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "text-primary",
								children: "S1"
							}),
							" PRE-SCREEN",
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "text-border",
								children: "›"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "text-primary",
								children: "S2"
							}),
							" TILE-SEG",
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "text-border",
								children: "›"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "text-primary",
								children: "S3"
							}),
							" CONTEXT"
						]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", { className: "h-4 w-px bg-border" }),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "font-mono text-[10px] text-muted-foreground",
						children: "v2.0"
					})
				]
			})]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "grid flex-1 grid-cols-1 overflow-hidden xl:grid-cols-[300px_minmax(0,1fr)_400px]",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ControlSidebar, {
					imageName: state.imageName,
					stage: state.stage,
					message: state.message,
					payload: state.payload,
					filters: state.filters,
					viewStage: state.viewStage,
					onImage,
					onRun: run,
					onReset: reset,
					onFilters: setFilters,
					onViewStage: setViewStage,
					enableStage1: state.enableStage1,
					enableStage2: state.enableStage2,
					enableStage3: state.enableStage3,
					onStageToggles: setStageToggles
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("main", {
					className: "flex min-h-[500px] flex-col overflow-hidden border-border xl:border-x",
					children: state.imageUrl && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(InspectionCanvas, {
						imageUrl: state.imageUrl,
						payload: state.payload,
						visibleDefects: filteredDefects,
						hoveredId,
						onHover: setHoveredId,
						viewStage: state.viewStage
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("section", {
					className: "flex min-h-[400px] flex-col overflow-hidden bg-sidebar/40",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "border-b border-border p-4",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "font-mono text-[10px] font-semibold uppercase tracking-widest text-muted-foreground",
								children: "Zone C · Diagnostics"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
								className: "mt-0.5 text-sm font-semibold uppercase tracking-wide",
								children: "Defect gallery & report"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "p-4 pb-0",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SummaryCard, {
								payload: state.payload,
								filteredCount: filteredDefects.length,
								disabledStages: state.payload?.disabled_stages ?? [
									...state.enableStage1 ? [] : ["stage1"],
									...state.enableStage2 ? [] : ["stage2"],
									...state.enableStage3 ? [] : ["stage3"]
								]
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "min-h-0 flex-1",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DefectGallery, {
								defects: filteredDefects,
								imageUrl: state.imageUrl ?? "/assets/demo-vehicle-QX9El2ws.jpg",
								inspectionId: state.payload?.inspection_id ?? null,
								hoveredId,
								unclassified_anomalies: state.payload?.unclassified_anomalies,
								suppressed_detections: state.payload?.suppressed_detections,
								onHover: setHoveredId,
								empty: state.payload?.inspection_status === "PASS" ? "Pre-screen returned PASS. No heavy processing triggered." : state.payload ? "No defects match the current filters." : "Run an inspection to populate the gallery."
							})
						})
					]
				})
			]
		})]
	});
}
//#endregion
export { InspectionDashboard as component };
