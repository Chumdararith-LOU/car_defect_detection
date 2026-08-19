import { n as __toESM } from "../_runtime.mjs";
import { C as fetchHostProfile } from "./apiClient-ClfACpV5.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { j as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { n as PageShell, t as PageHeader } from "./PageShell-CQ88Jn3b.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/host-CvKyd4Z0.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function HostPage() {
	const [profile, setProfile] = (0, import_react.useState)(null);
	const [error, setError] = (0, import_react.useState)(null);
	const [loading, setLoading] = (0, import_react.useState)(true);
	(0, import_react.useEffect)(() => {
		fetchHostProfile().then(setProfile).catch((err) => setError(err.message)).finally(() => setLoading(false));
	}, []);
	if (loading) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageShell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
		className: "font-mono text-[10px] uppercase tracking-widest text-muted-foreground",
		children: "Loading host profile..."
	}) });
	if (error) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageShell, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "rounded-sm border border-destructive/30 bg-destructive/10 p-4",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
			className: "font-mono text-[10px] uppercase tracking-widest text-destructive",
			children: ["Error: ", error]
		})
	}) });
	if (!profile) return null;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(PageShell, { children: [
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
			title: "Host",
			subtitle: "Hardware detection and runtime capabilities"
		}),
		profile.warnings.length > 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "rounded-sm border border-yellow-500/30 bg-yellow-500/10 p-3",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "font-mono text-[10px] uppercase tracking-widest text-yellow-600 mb-1",
				children: "Warnings"
			}), profile.warnings.map((w, i) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
				className: "font-mono text-[10px] text-yellow-600",
				children: ["• ", w]
			}, i))]
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
					title: "Machine",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
							label: "Hostname",
							value: profile.machine.hostname
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
							label: "OS",
							value: profile.machine.os
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
							label: "Platform",
							value: profile.machine.platform
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
							label: "Arch",
							value: profile.machine.architecture
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
							label: "Python",
							value: profile.machine.python_version
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
					title: "Compute",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
							label: "CPU Cores",
							value: `${profile.cpu.physical_cores}P / ${profile.cpu.logical_cores}L`
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
							label: "RAM",
							value: `${profile.memory.available_gb.toFixed(1)} / ${profile.memory.total_gb.toFixed(1)} GB free`
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
							label: "Disk",
							value: `${profile.disk.free_gb.toFixed(1)} / ${profile.disk.total_gb.toFixed(1)} GB free`
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
					title: "GPU",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
							label: "CUDA",
							value: profile.gpu.cuda_available ? "Available" : "Not available"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
							label: "MPS",
							value: profile.gpu.mps_available ? "Available" : "Not available"
						}),
						profile.gpu.devices.map((dev) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "mt-2 pt-2 border-t border-border",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
								label: `Device ${dev.index}`,
								value: dev.name
							}), dev.total_vram_gb !== null && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
								label: "VRAM",
								value: `${(dev.free_vram_gb ?? 0).toFixed(1)} / ${dev.total_vram_gb.toFixed(1)} GB`
							})]
						}, dev.index))
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
					title: "Model Availability",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ModelRow, {
							label: "Stage 1 (SOD)",
							available: profile.models.stage1.available
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ModelRow, {
							label: "Stage 2 (Defect)",
							available: profile.models.stage2.available
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ModelRow, {
							label: "Stage 3 (Panel)",
							available: profile.models.stage3.available
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ModelRow, {
							label: "Stage 4 (Fusion)",
							available: profile.models.stage4.available
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
					title: "Capabilities",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(BoolRow, {
							label: "Infer Stage 1",
							value: profile.capabilities.can_infer_stage1
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(BoolRow, {
							label: "Infer Stage 2",
							value: profile.capabilities.can_infer_stage2
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(BoolRow, {
							label: "Infer Stage 3",
							value: profile.capabilities.can_infer_stage3
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(BoolRow, {
							label: "Local GPU",
							value: profile.capabilities.can_use_local_gpu
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, {
					title: "Recommendations",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
							label: "Runtime Mode",
							value: profile.recommendations.runtime_mode
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
							label: "Inference Device",
							value: profile.recommendations.inference_device
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Row, {
							label: "Training Device",
							value: profile.recommendations.training_device
						})
					]
				})
			]
		})
	] });
}
function Card({ title, children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "rounded-sm border border-border bg-card p-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
			className: "font-mono text-[10px] uppercase tracking-widest text-muted-foreground mb-3",
			children: title
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "space-y-1.5",
			children
		})]
	});
}
function Row({ label, value }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex justify-between items-center",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
			className: "font-mono text-[10px] text-muted-foreground",
			children: label
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
			className: "font-mono text-[10px] text-foreground",
			children: value
		})]
	});
}
function ModelRow({ label, available }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex justify-between items-center",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
			className: "font-mono text-[10px] text-muted-foreground",
			children: label
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
			className: `font-mono text-[10px] ${available ? "text-green-500" : "text-red-500"}`,
			children: available ? "● Available" : "○ Missing"
		})]
	});
}
function BoolRow({ label, value }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "flex justify-between items-center",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
			className: "font-mono text-[10px] text-muted-foreground",
			children: label
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
			className: `font-mono text-[10px] ${value ? "text-green-500" : "text-muted-foreground"}`,
			children: value ? "Yes" : "No"
		})]
	});
}
//#endregion
export { HostPage as component };
