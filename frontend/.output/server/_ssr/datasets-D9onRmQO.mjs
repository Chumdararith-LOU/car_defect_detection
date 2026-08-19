import { n as __toESM } from "../_runtime.mjs";
import { E as fetchSplitStructure, F as importDatasetZip, G as reclassifyAnnotation, I as importInspectionToDataset, L as importZipToDataset, N as getDatasetImageUrl, Y as runFullDatasetAudit, Z as runLeakageAudit, _ as fetchDatasetDetail, a as deleteAnnotation, b as fetchDatasets, g as fetchDatasetAuditReport, m as fetchAvailableInspections, n as createNewDataset, p as fetchAllReviews, q as resplitDataset, rt as tileDataset, s as deleteDataset, t as buildDataset, v as fetchDatasetImageLabels, y as fetchDatasetImages } from "./apiClient-ClfACpV5.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { j as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { t as Button } from "./button-BkEeRci-.mjs";
import { l as StatusBadge } from "./alert-dialog-DsQ-Uqlb.mjs";
import { t as ConfirmDialog } from "./ConfirmDialog-CbIeVXtH.mjs";
import { B as ChevronRight, C as Hammer, D as FileQuestionMark, I as CircleX, J as ArrowLeft, K as Award, L as CircleCheck, O as Eye, R as CircleCheckBig, T as FlaskConical, V as ChevronLeft, X as Archive, a as TriangleAlert, b as Layers, c as Shuffle, g as Pencil, j as Database, k as EyeOff, l as ShieldCheck, m as Plus, n as X, o as Trash2, r as Upload, u as ShieldAlert, v as LoaderCircle, w as Folder, x as Image, y as LayoutGrid } from "../_libs/lucide-react.mjs";
import { a as DialogHeader, i as DialogFooter, n as DialogContent, o as DialogTitle, r as DialogDescription, s as EmptyState, t as Dialog } from "./dialog-BTaDPjwY.mjs";
import { i as CardTitle, n as CardContent, r as CardHeader, t as Card } from "./card-BXjpJ96D.mjs";
import { n as toast } from "../_libs/sonner.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/datasets-D9onRmQO.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
function getStageBadgeTone(stage) {
	switch (stage) {
		case "stage1": return "blue";
		case "stage2": return "purple";
		case "stage3": return "emerald";
		default: return "gray";
	}
}
function getStatusBadgeTone(status) {
	switch (status) {
		case "released": return "green";
		case "curated": return "yellow";
		case "raw": return "gray";
		case "archived": return "red";
		default: return "gray";
	}
}
function DatasetListView({ datasets, onSelect }) {
	if (datasets.length === 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EmptyState, {
		title: "No datasets found",
		hint: "Nothing in data/processed/ yet."
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "rounded-lg border border-border bg-card overflow-hidden",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("table", {
			className: "w-full text-sm",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("thead", {
				className: "bg-muted/50 border-b border-border",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
					className: "text-left text-[11px] font-mono uppercase tracking-wider text-muted-foreground",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-4 py-2.5",
							children: "Name"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-4 py-2.5",
							children: "Stage"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-4 py-2.5 text-right",
							children: "Images"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-4 py-2.5 text-right",
							children: "Classes"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", {
							className: "px-4 py-2.5",
							children: "Status"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("th", { className: "px-4 py-2.5 w-10" })
					]
				})
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("tbody", {
				className: "divide-y divide-border",
				children: datasets.map((ds) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("tr", {
					onClick: () => onSelect(ds.dataset_id),
					className: "hover:bg-muted/30 cursor-pointer transition-colors",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-4 py-3",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "flex items-center gap-2",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "font-medium",
									children: ds.name
								}), ds.is_champion && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Award, { className: "h-3.5 w-3.5 text-yellow-500" })]
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-4 py-3",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatusBadge, {
								tone: getStageBadgeTone(ds.stage),
								uppercase: true,
								children: ds.stage
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-4 py-3 text-right font-mono",
							children: ds.total_images.toLocaleString()
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-4 py-3 text-right font-mono",
							children: ds.nc
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-4 py-3",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(StatusBadge, {
								tone: getStatusBadgeTone(ds.status),
								className: "capitalize",
								children: ds.status
							})
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("td", {
							className: "px-4 py-3 text-right",
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ChevronRight, { className: "h-4 w-4 text-muted-foreground" })
						})
					]
				}, ds.dataset_id))
			})]
		})
	});
}
var COLORS$1 = [
	"bg-blue-500",
	"bg-emerald-500",
	"bg-amber-500",
	"bg-rose-500",
	"bg-violet-500",
	"bg-cyan-500",
	"bg-pink-500",
	"bg-lime-500",
	"bg-orange-500",
	"bg-teal-500",
	"bg-indigo-500",
	"bg-yellow-500"
];
function ClassDistributionBar({ distribution }) {
	if (!distribution || distribution.length === 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
		className: "text-xs text-muted-foreground",
		children: "No distribution data."
	});
	const nonZero = distribution.filter((d) => d.instance_count > 0);
	const totalInstances = nonZero.reduce((sum, d) => sum + d.instance_count, 0);
	if (totalInstances === 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
		className: "text-xs text-muted-foreground",
		children: "No instances found in label files."
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-3",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "flex h-4 w-full overflow-hidden rounded-md border border-border bg-muted/30",
			children: nonZero.map((item) => {
				const widthPct = item.instance_count / totalInstances * 100;
				const colorClass = COLORS$1[item.class_id % COLORS$1.length];
				return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: `h-full ${colorClass} transition-all`,
					style: { width: `${widthPct}%` },
					title: `${item.class_name}: ${item.instance_count} (${item.percentage}%)`
				}, item.class_id);
			})
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-x-4 gap-y-1.5 text-xs",
			children: distribution.map((item) => {
				const colorClass = COLORS$1[item.class_id % COLORS$1.length];
				return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center gap-1.5",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { className: `inline-block h-2.5 w-2.5 rounded-sm ${colorClass}` }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
							className: "font-medium text-foreground truncate",
							children: item.class_name
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "text-muted-foreground",
							children: [
								item.instance_count,
								" (",
								item.percentage,
								"%)"
							]
						})
					]
				}, item.class_id);
			})
		})]
	});
}
function LeakageAuditPanel({ datasetId }) {
	const [result, setResult] = (0, import_react.useState)(null);
	const [loading, setLoading] = (0, import_react.useState)(false);
	const [error, setError] = (0, import_react.useState)(null);
	const handleAudit = async () => {
		setLoading(true);
		setError(null);
		try {
			setResult(await runLeakageAudit(datasetId));
		} catch (err) {
			setError(err.message || "Audit failed");
		} finally {
			setLoading(false);
		}
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "rounded-lg border border-border bg-card p-4 space-y-3",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h4", {
					className: "text-sm font-semibold",
					children: "Leakage Audit"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "outline",
					size: "sm",
					onClick: handleAudit,
					disabled: loading,
					children: loading ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-3.5 w-3.5 mr-1.5 animate-spin" }), "Auditing..."] }) : "Run Filename Audit"
				})]
			}),
			error && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
				className: "text-xs text-destructive",
				children: ["Error: ", error]
			}),
			result && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-2 text-xs",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: `flex items-center gap-2 font-medium ${result.passed ? "text-green-600 dark:text-green-400" : "text-red-600 dark:text-red-400"}`,
						children: [result.passed ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ShieldCheck, { className: "h-4 w-4" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ShieldAlert, { className: "h-4 w-4" }), result.passed ? "Passed: No filename leakage detected" : "Failed: Filename overlaps found"]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
						className: "text-muted-foreground",
						children: [
							"Checked ",
							result.total_checked,
							" images across train/val/test splits."
						]
					}),
					!result.passed && result.filename_overlaps.length > 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "mt-2 max-h-32 overflow-y-auto rounded border border-border bg-background p-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "font-medium mb-1",
							children: [
								"Overlapping files (",
								result.filename_overlaps.length,
								"):"
							]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("ul", {
							className: "list-disc list-inside font-mono text-[10px] space-y-0.5",
							children: [result.filename_overlaps.slice(0, 10).map((o) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", { children: [
								o.filename,
								" ",
								/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
									className: "text-muted-foreground",
									children: [
										"(",
										o.found_in.join(", "),
										")"
									]
								})
							] }, o.filename)), result.filename_overlaps.length > 10 && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("li", {
								className: "text-muted-foreground",
								children: [
									"...and ",
									result.filename_overlaps.length - 10,
									" more"
								]
							})]
						})]
					})
				]
			})
		]
	});
}
var COLORS = [
	"#3b82f6",
	"#10b981",
	"#f59e0b",
	"#ef4444",
	"#8b5cf6",
	"#06b6d4",
	"#ec4899",
	"#84cc16"
];
function MaskOverlay({ annotations, width, height, visible }) {
	if (!visible || annotations.length === 0 || width === 0 || height === 0) return null;
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("svg", {
		className: "absolute inset-0 pointer-events-none",
		viewBox: `0 0 ${width} ${height}`,
		preserveAspectRatio: "xMidYMid meet",
		children: annotations.map((ann) => {
			const color = COLORS[ann.class_id % COLORS.length];
			return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("g", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("polygon", {
				points: ann.polygon.map(([x, y]) => `${x * width},${y * height}`).join(" "),
				fill: color,
				fillOpacity: .3,
				stroke: color,
				strokeWidth: 2
			}), ann.polygon.length > 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("text", {
				x: ann.polygon[0][0] * width,
				y: ann.polygon[0][1] * height - 4,
				fill: "white",
				fontSize: "14",
				fontWeight: "bold",
				style: { textShadow: "1px 1px 2px black" },
				children: ann.class_name
			})] }, ann.index);
		})
	});
}
function ReclassifyDialog({ classNames, currentClassId, onConfirm, onCancel }) {
	const [selectedClass, setSelectedClass] = (0, import_react.useState)(currentClassId);
	const [saving, setSaving] = (0, import_react.useState)(false);
	const [error, setError] = (0, import_react.useState)(null);
	const handleConfirm = async () => {
		setSaving(true);
		setError(null);
		try {
			await onConfirm(selectedClass);
		} catch (err) {
			setError(err.message || "Failed to reclassify");
		} finally {
			setSaving(false);
		}
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "fixed inset-0 z-[60] flex items-center justify-center bg-black/50",
		onClick: onCancel,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "w-80 rounded-lg border border-border bg-card p-5 shadow-xl space-y-4",
			onClick: (e) => e.stopPropagation(),
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h4", {
					className: "text-sm font-semibold",
					children: "Reclassify Annotation"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-1.5",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "text-xs text-muted-foreground",
						children: "Current class"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-sm font-mono font-medium",
						children: classNames[currentClassId] || `class_${currentClassId}`
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-1.5",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "text-xs text-muted-foreground",
						children: "New class"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("select", {
						value: selectedClass,
						onChange: (e) => setSelectedClass(Number(e.target.value)),
						className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
						children: classNames.map((name, idx) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
							value: idx,
							children: name
						}, idx))
					})]
				}),
				error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-xs text-destructive",
					children: error
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex justify-end gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "ghost",
						size: "sm",
						onClick: onCancel,
						children: "Cancel"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						size: "sm",
						onClick: handleConfirm,
						disabled: saving || selectedClass === currentClassId,
						children: saving ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-3.5 w-3.5 mr-1 animate-spin" }), "Saving..."] }) : "Reclassify"
					})]
				})
			]
		})
	});
}
function ImageViewer({ datasetId, filename, onClose }) {
	const [annotations, setAnnotations] = (0, import_react.useState)([]);
	const [classNames, setClassNames] = (0, import_react.useState)([]);
	const [showMasks, setShowMasks] = (0, import_react.useState)(true);
	const [imgDims, setImgDims] = (0, import_react.useState)({
		width: 800,
		height: 600
	});
	const [reclassifyIndex, setReclassifyIndex] = (0, import_react.useState)(null);
	const loadLabels = () => {
		fetchDatasetImageLabels(datasetId, filename).then((res) => {
			setAnnotations(res.annotations);
			setClassNames(res.class_names || []);
		}).catch((err) => console.error(err));
	};
	(0, import_react.useEffect)(() => {
		loadLabels();
	}, [datasetId, filename]);
	const handleImageLoad = (e) => {
		const img = e.currentTarget;
		setImgDims({
			width: img.naturalWidth,
			height: img.naturalHeight
		});
	};
	const imageUrl = getDatasetImageUrl(datasetId, filename);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-8",
		onClick: onClose,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "relative flex max-h-full max-w-5xl flex-col overflow-hidden rounded-lg bg-card shadow-2xl border border-border",
			onClick: (e) => e.stopPropagation(),
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center justify-between border-b border-border p-3",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
						className: "font-mono text-sm font-medium truncate",
						children: filename
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center gap-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
							variant: "ghost",
							size: "sm",
							onClick: () => setShowMasks(!showMasks),
							children: [showMasks ? /* @__PURE__ */ (0, import_jsx_runtime.jsx)(EyeOff, { className: "h-4 w-4 mr-1" }) : /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Eye, { className: "h-4 w-4 mr-1" }), showMasks ? "Hide Masks" : "Show Masks"]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
							variant: "ghost",
							size: "icon",
							onClick: onClose,
							children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, { className: "h-5 w-5" })
						})]
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "relative flex-1 overflow-auto bg-muted/20 p-4 flex items-center justify-center",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "relative inline-block",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("img", {
							src: imageUrl,
							alt: filename,
							onLoad: handleImageLoad,
							className: "max-h-[70vh] w-auto rounded shadow-lg"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(MaskOverlay, {
							annotations,
							width: imgDims.width,
							height: imgDims.height,
							visible: showMasks
						})]
					})
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "border-t border-border p-3 flex flex-wrap items-center gap-2 text-xs",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
						className: "text-muted-foreground font-medium",
						children: [
							"Annotations (",
							annotations.length,
							"):"
						]
					}), annotations.map((ann) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
						className: "inline-flex items-center gap-1.5 px-2 py-0.5 rounded bg-muted font-mono",
						children: [
							ann.class_name,
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
								onClick: () => setReclassifyIndex(ann.index),
								className: "text-muted-foreground hover:text-blue-500 transition-colors",
								title: "Reclassify",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Pencil, { className: "h-3 w-3" })
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
								onClick: async () => {
									if (!confirm(`Delete this ${ann.class_name} annotation? (False Positive)`)) return;
									try {
										await deleteAnnotation(datasetId, filename, ann.index);
										loadLabels();
									} catch (err) {
										alert(err.message);
									}
								},
								className: "text-muted-foreground hover:text-red-500 transition-colors",
								title: "Delete annotation (False Positive)",
								children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Trash2, { className: "h-3 w-3" })
							})
						]
					}, ann.index))]
				}),
				reclassifyIndex !== null && classNames.length > 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ReclassifyDialog, {
					classNames,
					currentClassId: annotations.find((a) => a.index === reclassifyIndex)?.class_id ?? 0,
					onConfirm: async (newClassId) => {
						await reclassifyAnnotation(datasetId, filename, reclassifyIndex, newClassId);
						setReclassifyIndex(null);
						loadLabels();
					},
					onCancel: () => setReclassifyIndex(null)
				})
			]
		})
	});
}
function ImageGallery({ datasetId }) {
	const [images, setImages] = (0, import_react.useState)([]);
	const [page, setPage] = (0, import_react.useState)(1);
	const [totalPages, setTotalPages] = (0, import_react.useState)(0);
	const [totalImages, setTotalImages] = (0, import_react.useState)(0);
	const [loading, setLoading] = (0, import_react.useState)(true);
	const [selectedImage, setSelectedImage] = (0, import_react.useState)(null);
	(0, import_react.useEffect)(() => {
		const load = async () => {
			setLoading(true);
			try {
				const res = await fetchDatasetImages(datasetId, page, 20);
				setImages(res.images);
				setTotalPages(res.total_pages);
				setTotalImages(res.total);
			} catch (err) {
				console.error(err);
			} finally {
				setLoading(false);
			}
		};
		load();
	}, [datasetId, page]);
	if (loading && images.length === 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "p-8 text-center text-muted-foreground",
		children: "Loading images..."
	});
	if (totalImages === 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "p-8 text-center text-muted-foreground border border-border rounded-lg bg-card",
		children: "No images found in this dataset split."
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3",
				children: images.map((filename) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
					onClick: () => setSelectedImage(filename),
					className: "group relative aspect-square overflow-hidden rounded-md border border-border bg-muted/30 hover:border-primary transition-colors",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("img", {
						src: getDatasetImageUrl(datasetId, filename),
						alt: filename,
						className: "h-full w-full object-cover transition-transform group-hover:scale-105",
						loading: "lazy"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "absolute inset-x-0 bottom-0 bg-black/60 p-1.5 opacity-0 group-hover:opacity-100 transition-opacity",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-[10px] text-white font-mono truncate",
							children: filename
						})
					})]
				}, filename))
			}),
			totalPages > 1 && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between text-sm",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "text-muted-foreground",
					children: [
						"Showing ",
						(page - 1) * 20 + 1,
						"–",
						Math.min(page * 20, totalImages),
						" of ",
						totalImages
					]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center gap-2",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
							variant: "outline",
							size: "sm",
							disabled: page <= 1,
							onClick: () => setPage((p) => p - 1),
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ChevronLeft, { className: "h-4 w-4" }), " Prev"]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "font-mono text-xs",
							children: [
								"Page ",
								page,
								" of ",
								totalPages
							]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
							variant: "outline",
							size: "sm",
							disabled: page >= totalPages,
							onClick: () => setPage((p) => p + 1),
							children: ["Next ", /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ChevronRight, { className: "h-4 w-4" })]
						})
					]
				})]
			}),
			selectedImage && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ImageViewer, {
				datasetId,
				filename: selectedImage,
				onClose: () => setSelectedImage(null)
			})
		]
	});
}
function InspectionPicker({ datasetId, onComplete }) {
	const [inspections, setInspections] = (0, import_react.useState)([]);
	const [loading, setLoading] = (0, import_react.useState)(true);
	const [importingId, setImportingId] = (0, import_react.useState)(null);
	const [successId, setSuccessId] = (0, import_react.useState)(null);
	const [split, setSplit] = (0, import_react.useState)("train");
	(0, import_react.useEffect)(() => {
		fetchAvailableInspections().then((res) => setInspections(res.inspections)).catch((err) => console.error(err)).finally(() => setLoading(false));
	}, []);
	const handleImport = async (inspectionId) => {
		setImportingId(inspectionId);
		try {
			await importInspectionToDataset(datasetId, inspectionId, split);
			setSuccessId(inspectionId);
			setTimeout(() => setSuccessId(null), 2e3);
			onComplete();
		} catch (err) {
			alert(err.message);
		} finally {
			setImportingId(null);
		}
	};
	if (loading) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
		className: "text-sm text-muted-foreground",
		children: "Loading saved inspections..."
	});
	if (inspections.length === 0) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
		className: "text-sm text-muted-foreground",
		children: "No saved inspections found. Run an inspection first."
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-3",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "flex items-center gap-2 text-sm",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
				className: "font-medium",
				children: "Target Split:"
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("select", {
				value: split,
				onChange: (e) => setSplit(e.target.value),
				className: "rounded border border-input bg-background px-2 py-1 text-xs",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
						value: "train",
						children: "train"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
						value: "val",
						children: "val"
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
						value: "test",
						children: "test"
					})
				]
			})]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "max-h-64 overflow-y-auto rounded border border-border divide-y divide-border",
			children: inspections.map((insp) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between p-3 text-sm hover:bg-muted/30",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "font-mono text-xs font-medium",
					children: insp.inspection_id
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "text-xs text-muted-foreground",
					children: [
						insp.defect_count,
						" defects • ",
						insp.inspection_status,
						" • ",
						new Date(insp.timestamp).toLocaleDateString()
					]
				})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					size: "sm",
					variant: successId === insp.inspection_id ? "default" : "outline",
					onClick: () => handleImport(insp.inspection_id),
					disabled: importingId !== null || successId === insp.inspection_id,
					children: importingId === insp.inspection_id ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-3 w-3 mr-1 animate-spin" }), " Importing..."] }) : successId === insp.inspection_id ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CircleCheckBig, { className: "h-3 w-3 mr-1" }), " Imported"] }) : "Import"
				})]
			}, insp.inspection_id))
		})]
	});
}
function ZipUploader({ datasetId, onComplete }) {
	const [file, setFile] = (0, import_react.useState)(null);
	const [split, setSplit] = (0, import_react.useState)("train");
	const [uploading, setUploading] = (0, import_react.useState)(false);
	const [successMsg, setSuccessMsg] = (0, import_react.useState)(null);
	const [error, setError] = (0, import_react.useState)(null);
	const handleUpload = async () => {
		if (!file) return;
		setUploading(true);
		setError(null);
		setSuccessMsg(null);
		try {
			setSuccessMsg((await importZipToDataset(datasetId, file, split)).message);
			setFile(null);
			onComplete();
		} catch (err) {
			setError(err.message || "Upload failed");
		} finally {
			setUploading(false);
		}
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
				className: "text-xs text-muted-foreground",
				children: [
					"Upload a ZIP archive containing image files (",
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("code", { children: ".jpg" }),
					", ",
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("code", { children: ".png" }),
					") and their corresponding YOLO label files (",
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)("code", { children: ".txt" }),
					")."
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-end gap-4",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex-1 space-y-1.5",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "text-sm font-medium",
						children: "Select ZIP Archive"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
						type: "file",
						accept: ".zip,application/zip",
						onChange: (e) => setFile(e.target.files?.[0] || null),
						className: "block w-full text-sm text-muted-foreground file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-primary/10 file:text-primary hover:file:bg-primary/20"
					})]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-1.5",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "text-sm font-medium",
						children: "Split"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("select", {
						value: split,
						onChange: (e) => setSplit(e.target.value),
						className: "block w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "train",
								children: "train"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "val",
								children: "val"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
								value: "test",
								children: "test"
							})
						]
					})]
				})]
			}),
			error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-xs text-destructive",
				children: error
			}),
			successMsg && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
				className: "text-xs text-green-600 dark:text-green-400 flex items-center gap-1",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CircleCheckBig, { className: "h-3.5 w-3.5" }),
					" ",
					successMsg
				]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
				onClick: handleUpload,
				disabled: !file || uploading,
				className: "w-full",
				children: uploading ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-4 w-4 mr-2 animate-spin" }), " Extracting & Importing..."] }) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Archive, { className: "h-4 w-4 mr-2" }),
					" Import ZIP to ",
					split
				] })
			})
		]
	});
}
function ImportPanel({ datasetId, onImportComplete }) {
	const [mode, setMode] = (0, import_react.useState)("flywheel");
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "rounded-lg border border-border bg-card p-5 space-y-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
				className: "text-base font-semibold flex items-center gap-2",
				children: "Import Images"
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex gap-2 border-b border-border pb-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
					onClick: () => setMode("flywheel"),
					className: `flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-t-md transition-colors ${mode === "flywheel" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"}`,
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Database, { className: "h-4 w-4" }), " From Flywheel"]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
					onClick: () => setMode("zip"),
					className: `flex items-center gap-1.5 px-3 py-1.5 text-sm rounded-t-md transition-colors ${mode === "zip" ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted"}`,
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Archive, { className: "h-4 w-4" }), " Upload ZIP"]
				})]
			}),
			mode === "flywheel" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(InspectionPicker, {
				datasetId,
				onComplete: onImportComplete
			}),
			mode === "zip" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ZipUploader, {
				datasetId,
				onComplete: onImportComplete
			})
		]
	});
}
function DatasetAuditReport({ report, loading, running, error, onRun }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-3 rounded-lg border border-border bg-card p-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h3", {
					className: "flex items-center gap-2 text-sm font-semibold",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(FlaskConical, { className: "h-4 w-4 text-muted-foreground" }), "Training Readiness Audit"]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					size: "sm",
					variant: "outline",
					onClick: onRun,
					disabled: running || loading,
					children: running ? "Auditing..." : report ? "Re-run Full Audit" : "Run Full Audit"
				})]
			}),
			error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-xs text-destructive",
				children: error
			}),
			loading && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-xs text-muted-foreground",
				children: "Loading audit report..."
			}),
			!loading && !report && !error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-xs text-muted-foreground",
				children: "No audit report yet. Run the full audit to check size buckets, label validity, and training clearance."
			}),
			report && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-4",
				children: [
					report.cleared_for_training ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex items-center gap-2 rounded-md border border-status-pass/30 bg-status-pass/10 p-3 text-xs text-status-pass",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CircleCheck, { className: "h-4 w-4 shrink-0" }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { children: ["Cleared for training · computed ", new Date(report.computed_at).toLocaleString()] })]
					}) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "rounded-md border border-status-fail/30 bg-status-fail/10 p-3 text-xs text-status-fail",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "flex items-center gap-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CircleX, { className: "h-4 w-4 shrink-0" }), "Blocked for training"]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("ul", {
							className: "mt-1 list-disc space-y-0.5 pl-6",
							children: report.blocking_reasons.map((r) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { children: r }, r))
						})]
					}),
					report.warnings.length > 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "rounded-md border border-amber-500/30 bg-amber-500/10 p-3 text-xs text-amber-700 dark:text-amber-400",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "flex items-center gap-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TriangleAlert, { className: "h-4 w-4 shrink-0" }), "Warnings"]
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("ul", {
							className: "mt-1 list-disc space-y-0.5 pl-6",
							children: report.warnings.map((w) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("li", { children: w }, w))
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid grid-cols-3 gap-2 md:grid-cols-6",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "rounded-md border border-border bg-muted/30 p-2 text-center",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-[10px] font-mono uppercase text-muted-foreground",
									children: "Images"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "font-mono text-sm font-semibold",
									children: report.totals.images.toLocaleString()
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "rounded-md border border-border bg-muted/30 p-2 text-center",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-[10px] font-mono uppercase text-muted-foreground",
									children: "Instances"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "font-mono text-sm font-semibold",
									children: report.totals.instances.toLocaleString()
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "rounded-md border border-border bg-muted/30 p-2 text-center",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-[10px] font-mono uppercase text-muted-foreground",
									children: "Missing lbl"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "font-mono text-sm font-semibold",
									children: report.label_issues.missing_label_images
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "rounded-md border border-border bg-muted/30 p-2 text-center",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-[10px] font-mono uppercase text-muted-foreground",
									children: "Empty lbl"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "font-mono text-sm font-semibold",
									children: report.label_issues.empty_label_images
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "rounded-md border border-border bg-muted/30 p-2 text-center",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-[10px] font-mono uppercase text-muted-foreground",
									children: "Bad lines"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "font-mono text-sm font-semibold",
									children: report.label_issues.unparseable_lines
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "rounded-md border border-border bg-muted/30 p-2 text-center",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-[10px] font-mono uppercase text-muted-foreground",
									children: "Bad ids"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "font-mono text-sm font-semibold",
									children: report.label_issues.out_of_range_class_ids
								})]
							})
						]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "space-y-1",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h4", {
								className: "text-xs font-semibold",
								children: "Annotation size buckets (relative area)"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "grid grid-cols-3 gap-2 text-center",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
										className: "rounded-md border border-border bg-muted/30 p-2",
										children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
											className: "text-[10px] font-mono uppercase text-muted-foreground",
											children: "Bottom 10%"
										}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
											className: "font-mono text-sm font-semibold",
											children: report.size_buckets.bottom_10_count
										})]
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
										className: "rounded-md border border-border bg-muted/30 p-2",
										children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
											className: "text-[10px] font-mono uppercase text-muted-foreground",
											children: "Middle 50%"
										}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
											className: "font-mono text-sm font-semibold",
											children: report.size_buckets.middle_50_count
										})]
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
										className: "rounded-md border border-border bg-muted/30 p-2",
										children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
											className: "text-[10px] font-mono uppercase text-muted-foreground",
											children: "Top 40%"
										}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
											className: "font-mono text-sm font-semibold",
											children: report.size_buckets.top_40_count
										})]
									})
								]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
								className: "font-mono text-[10px] text-muted-foreground",
								children: [
									"p10=",
									report.size_buckets.p10_area,
									" · p60=",
									report.size_buckets.p60_area
								]
							})
						]
					}),
					report.rare_classes.length > 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "space-y-1",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h4", {
							className: "text-xs font-semibold",
							children: "Rare classes"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "flex flex-wrap gap-1.5",
							children: report.rare_classes.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "rounded-sm border border-amber-500/30 bg-amber-500/10 px-1.5 py-0.5 font-mono text-[10px] text-amber-700 dark:text-amber-400",
								children: c
							}, c))
						})]
					}),
					report.stage === "stage1" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-[10px] text-muted-foreground",
						children: "Semantic-mask dataset — YOLO label checks skipped."
					})
				]
			})
		]
	});
}
var LAYOUT_BADGE = {
	ultralytics: {
		label: "Ultralytics",
		className: "bg-green-500/15 text-green-700 dark:text-green-400 border-green-500/30"
	},
	grouped: {
		label: "Grouped",
		className: "bg-blue-500/15 text-blue-700 dark:text-blue-400 border-blue-500/30"
	},
	unsplit: {
		label: "Unsplit",
		className: "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30"
	},
	flat: {
		label: "Flat",
		className: "bg-amber-500/15 text-amber-700 dark:text-amber-400 border-amber-500/30"
	},
	unknown: {
		label: "Unknown",
		className: "bg-red-500/15 text-red-700 dark:text-red-400 border-red-500/30"
	}
};
var GRID_COLS = {
	1: "grid-cols-1",
	2: "grid-cols-2",
	3: "grid-cols-3"
};
function SplitStructurePanel({ structure }) {
	const layout = LAYOUT_BADGE[structure.layout];
	const gridClass = GRID_COLS[structure.splits.length] ?? "grid-cols-3";
	const isSemantic = structure.splits.some((s) => s.label_format === "semantic_mask");
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex flex-wrap items-center justify-between gap-2",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
					className: `inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium ${layout.className}`,
					children: [layout.label, " layout"]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center gap-3 text-xs text-muted-foreground",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { children: [structure.total_images.toLocaleString(), " images"] }),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", { children: [
							structure.total_labels.toLocaleString(),
							" ",
							isSemantic ? "masks" : "labels"
						] }),
						structure.has_data_yaml ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "inline-flex items-center gap-1 text-green-600 dark:text-green-400",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CircleCheck, { className: "h-3 w-3" }), " data.yaml"]
						}) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "inline-flex items-center gap-1 text-amber-600 dark:text-amber-400",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(FileQuestionMark, { className: "h-3 w-3" }), " no data.yaml"]
						})
					]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-xs text-muted-foreground",
				children: structure.is_split ? structure.has_test ? "Already split into train / val / test." : "Already split into train / val." : "Not split yet — choose a ratio below to split before training."
			}),
			structure.splits.length > 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: `grid gap-2 ${gridClass}`,
				children: structure.splits.map((split) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "rounded-md border border-border bg-muted/30 p-3 text-center",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-[10px] font-mono uppercase tracking-wider text-muted-foreground",
							children: split.name
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-lg font-semibold",
							children: split.image_count.toLocaleString()
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "text-[10px] text-muted-foreground",
							children: [
								split.label_count.toLocaleString(),
								" ",
								split.label_format === "semantic_mask" ? "masks" : "labels"
							]
						})
					]
				}, split.name))
			}),
			structure.warnings.length > 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "space-y-1.5",
				children: structure.warnings.map((warning, idx) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-start gap-2 rounded-md border border-amber-500/30 bg-amber-500/10 px-3 py-2 text-xs text-amber-700 dark:text-amber-400",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(TriangleAlert, { className: "mt-0.5 h-3.5 w-3.5 shrink-0" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: warning })]
				}, idx))
			})
		]
	});
}
var RATIO_PRESETS = [
	{
		label: "80 / 20",
		train: .8,
		val: .2,
		test: 0
	},
	{
		label: "80 / 10 / 10",
		train: .8,
		val: .1,
		test: .1
	},
	{
		label: "70 / 20 / 10",
		train: .7,
		val: .2,
		test: .1
	},
	{
		label: "70 / 15 / 15",
		train: .7,
		val: .15,
		test: .15
	}
];
function ResplitDialog({ datasetId, totalImages, onClose, onComplete }) {
	const [trainRatio, setTrainRatio] = (0, import_react.useState)(.8);
	const [valRatio, setValRatio] = (0, import_react.useState)(.1);
	const [testRatio, setTestRatio] = (0, import_react.useState)(.1);
	const [seed, setSeed] = (0, import_react.useState)(42);
	const [submitting, setSubmitting] = (0, import_react.useState)(false);
	const [error, setError] = (0, import_react.useState)(null);
	const [result, setResult] = (0, import_react.useState)(null);
	const sum = trainRatio + valRatio + testRatio;
	const sumIsValid = Math.abs(sum - 1) < .001;
	const ratioFields = [
		{
			label: "Train",
			value: trainRatio,
			setter: setTrainRatio
		},
		{
			label: "Val",
			value: valRatio,
			setter: setValRatio
		},
		{
			label: "Test",
			value: testRatio,
			setter: setTestRatio
		}
	];
	const applyPreset = (preset) => {
		setTrainRatio(preset.train);
		setValRatio(preset.val);
		setTestRatio(preset.test);
		setError(null);
	};
	const handleResplit = async () => {
		if (!sumIsValid) return;
		setSubmitting(true);
		setError(null);
		try {
			setResult(await resplitDataset(datasetId, {
				train_ratio: trainRatio,
				val_ratio: valRatio,
				test_ratio: testRatio,
				seed
			}));
			onComplete();
		} catch (e) {
			setError(e instanceof Error ? e.message : "Failed to re-split dataset");
		} finally {
			setSubmitting(false);
		}
	};
	if (result) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dialog, {
		open: true,
		onOpenChange: (o) => {
			if (!o) onClose();
		},
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, {
			className: "max-w-lg space-y-4",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogHeader, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle, { children: "Re-split Complete" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogDescription, { children: result.message })] }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SplitStructurePanel, { structure: result.new_structure }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogFooter, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					onClick: onClose,
					children: "Done"
				}) })
			]
		})
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Dialog, {
		open: true,
		onOpenChange: (o) => {
			if (!o) onClose();
		},
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogContent, {
			className: "max-w-md space-y-4",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogHeader, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogTitle, { children: "Re-split Dataset" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DialogDescription, { children: "Choose train / val / test ratios and a seed." })] }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-1.5",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "text-sm font-medium",
						children: "Presets"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "flex flex-wrap gap-2",
						children: RATIO_PRESETS.map((preset) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
							onClick: () => applyPreset(preset),
							className: "rounded-md border border-border bg-muted/30 px-2.5 py-1.5 text-xs transition-colors hover:bg-muted",
							children: preset.label
						}, preset.label))
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "grid grid-cols-3 gap-2",
					children: ratioFields.map((field) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "space-y-1.5",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
							className: "text-xs font-medium text-muted-foreground",
							children: field.label
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
							type: "number",
							min: 0,
							max: 1,
							step: .05,
							value: field.value,
							onChange: (e) => field.setter(Number(e.target.value)),
							className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
						})]
					}, field.label))
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-1.5",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
							className: "text-sm font-medium",
							children: "Seed"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
							type: "number",
							value: seed,
							onChange: (e) => setSeed(Number(e.target.value)),
							className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-[11px] text-muted-foreground",
							children: "Same seed = same split every time."
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "rounded-md border border-border bg-muted/30 p-3 text-xs",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
						className: "mb-1 text-muted-foreground",
						children: [
							"Splitting ",
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
								className: "font-semibold",
								children: totalImages.toLocaleString()
							}),
							" images"
						]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
						className: "grid grid-cols-3 gap-2 text-center",
						children: ratioFields.map((field) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-muted-foreground",
							children: field.label
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "font-semibold",
							children: Math.round(totalImages * field.value).toLocaleString()
						})] }, field.label))
					})]
				}),
				!sumIsValid && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
					className: "text-xs text-destructive",
					children: [
						"Ratios must sum to 1.0 (current sum: ",
						sum.toFixed(2),
						")"
					]
				}),
				error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-xs text-destructive",
					children: error
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(DialogFooter, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					variant: "ghost",
					onClick: onClose,
					children: "Cancel"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
					onClick: handleResplit,
					disabled: !sumIsValid || submitting,
					children: submitting ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "mr-1.5 h-4 w-4 animate-spin" }), " Re-splitting..."] }) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Shuffle, { className: "mr-1.5 h-4 w-4" }), " Re-split Dataset"] })
				})] })
			]
		})
	});
}
var TILE_SIZE_PRESETS = [
	{
		label: "640",
		value: 640
	},
	{
		label: "1024",
		value: 1024
	},
	{
		label: "Adaptive 2×2",
		value: 0
	}
];
function TileDialog({ datasetId, sourceDatasetName, onClose, onComplete }) {
	const [newDatasetId, setNewDatasetId] = (0, import_react.useState)(`${sourceDatasetName}_tiled`);
	const [tileSize, setTileSize] = (0, import_react.useState)(1024);
	const [overlap, setOverlap] = (0, import_react.useState)(.15);
	const [minAreaRatio, setMinAreaRatio] = (0, import_react.useState)(.01);
	const [submitting, setSubmitting] = (0, import_react.useState)(false);
	const [error, setError] = (0, import_react.useState)(null);
	const [result, setResult] = (0, import_react.useState)(null);
	const handleTile = async () => {
		if (!newDatasetId.trim()) return;
		setSubmitting(true);
		setError(null);
		try {
			setResult(await tileDataset(datasetId, {
				new_dataset_id: newDatasetId.trim(),
				tile_size: tileSize,
				overlap,
				min_area_ratio: minAreaRatio
			}));
			onComplete();
		} catch (err) {
			setError(err.message || "Failed to tile dataset");
		} finally {
			setSubmitting(false);
		}
	};
	if (result) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "fixed inset-0 z-50 flex items-center justify-center bg-black/50",
		onClick: onClose,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "w-full max-w-md space-y-4 rounded-lg border border-border bg-card p-6 shadow-xl",
			onClick: (e) => e.stopPropagation(),
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center justify-between",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
						className: "text-lg font-semibold",
						children: "Tiling Complete"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						onClick: onClose,
						className: "text-muted-foreground hover:text-foreground",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, { className: "h-5 w-5" })
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-sm text-muted-foreground",
					children: result.message
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "rounded-md border border-border bg-muted/30 p-4 text-center",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-3xl font-semibold",
							children: result.tiles_generated.toLocaleString()
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "mt-1 text-xs text-muted-foreground",
							children: "tiles generated"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
							className: "mt-2 text-xs text-muted-foreground",
							children: [
								"New dataset:",
								" ",
								/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
									className: "font-mono",
									children: result.new_dataset_id
								})
							]
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "flex justify-end",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						onClick: onClose,
						children: "Done"
					})
				})
			]
		})
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "fixed inset-0 z-50 flex items-center justify-center bg-black/50",
		onClick: onClose,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "w-full max-w-md space-y-4 rounded-lg border border-border bg-card p-6 shadow-xl",
			onClick: (e) => e.stopPropagation(),
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center justify-between",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
						className: "text-lg font-semibold",
						children: "Tile Dataset"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						onClick: onClose,
						className: "text-muted-foreground hover:text-foreground",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, { className: "h-5 w-5" })
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-xs text-muted-foreground",
					children: "Creates a new dataset of image tiles. Use this before training Stage 1 (SOD) or to improve small-defect recall."
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-1.5",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
						className: "text-sm font-medium",
						children: "New Dataset Name"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
						type: "text",
						value: newDatasetId,
						onChange: (e) => setNewDatasetId(e.target.value),
						placeholder: "e.g. my_dataset_tiled",
						className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-1.5",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
							className: "text-sm font-medium",
							children: "Tile Size"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "flex flex-wrap gap-2",
							children: TILE_SIZE_PRESETS.map((preset) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
								onClick: () => setTileSize(preset.value),
								className: `rounded-md border px-2.5 py-1.5 text-xs transition-colors ${tileSize === preset.value ? "border-foreground bg-muted" : "border-border bg-muted/30 hover:bg-muted"}`,
								children: preset.label
							}, preset.label))
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
							type: "number",
							min: 0,
							step: 64,
							value: tileSize,
							onChange: (e) => setTileSize(Number(e.target.value)),
							className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
							className: "text-[11px] text-muted-foreground",
							children: tileSize === 0 ? "Adaptive mode: splits each image into 4 overlapping halves (legacy Stage 1 SOD)." : `Fixed ${tileSize}×${tileSize} pixel tiles.`
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "grid grid-cols-2 gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "space-y-1.5",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
								className: "text-xs font-medium text-muted-foreground",
								children: "Overlap"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
								type: "number",
								min: 0,
								max: .9,
								step: .05,
								value: overlap,
								onChange: (e) => setOverlap(Number(e.target.value)),
								className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
								className: "text-[11px] text-muted-foreground",
								children: [(overlap * 100).toFixed(0), "% overlap"]
							})
						]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "space-y-1.5",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
								className: "text-xs font-medium text-muted-foreground",
								children: "Min Area Ratio"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
								type: "number",
								min: 0,
								max: 1,
								step: .01,
								value: minAreaRatio,
								onChange: (e) => setMinAreaRatio(Number(e.target.value)),
								className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-[11px] text-muted-foreground",
								children: "Discard clipped fragments below this fraction"
							})
						]
					})]
				}),
				error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-xs text-destructive",
					children: error
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex justify-end gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						variant: "ghost",
						onClick: onClose,
						children: "Cancel"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						onClick: handleTile,
						disabled: !newDatasetId.trim() || submitting,
						children: submitting ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "mr-1.5 h-4 w-4 animate-spin" }), " Tiling..."] }) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LayoutGrid, { className: "mr-1.5 h-4 w-4" }), " Tile Dataset"] })
					})]
				})
			]
		})
	});
}
function DatasetPrepPanel({ datasetId, datasetName, totalImages, onPrepComplete }) {
	const [structure, setStructure] = (0, import_react.useState)(null);
	const [loading, setLoading] = (0, import_react.useState)(true);
	const [error, setError] = (0, import_react.useState)(null);
	const [showResplit, setShowResplit] = (0, import_react.useState)(false);
	const [showTile, setShowTile] = (0, import_react.useState)(false);
	const loadStructure = (0, import_react.useCallback)(async () => {
		try {
			setLoading(true);
			setError(null);
			setStructure(await fetchSplitStructure(datasetId));
		} catch (err) {
			setError(err.message || "Failed to detect split structure");
		} finally {
			setLoading(false);
		}
	}, [datasetId]);
	(0, import_react.useEffect)(() => {
		loadStructure();
	}, [loadStructure]);
	const handlePrepDone = () => {
		loadStructure();
		onPrepComplete();
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, { children: [
		/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardHeader, {
			className: "pb-3",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardTitle, {
					className: "text-lg",
					children: "Dataset Preparation"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
						variant: "outline",
						size: "sm",
						onClick: () => setShowResplit(true),
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Shuffle, { className: "mr-1.5 h-4 w-4" }), " Re-split"]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
						variant: "outline",
						size: "sm",
						onClick: () => setShowTile(true),
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LayoutGrid, { className: "mr-1.5 h-4 w-4" }), " Tile"]
					})]
				})]
			})
		}),
		/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(CardContent, { children: [
			loading && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center gap-2 text-sm text-muted-foreground",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-4 w-4 animate-spin" }), " Detecting split structure..."]
			}),
			error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "text-xs text-destructive",
				children: error
			}),
			!loading && !error && structure && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SplitStructurePanel, { structure })
		] }),
		showResplit && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ResplitDialog, {
			datasetId,
			totalImages,
			onClose: () => setShowResplit(false),
			onComplete: handlePrepDone
		}),
		showTile && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(TileDialog, {
			datasetId,
			sourceDatasetName: datasetName,
			onClose: () => setShowTile(false),
			onComplete: handlePrepDone
		})
	] });
}
function DatasetDetailPanel({ dataset, onBack, onDeleted }) {
	const [galleryKey, setGalleryKey] = (0, import_react.useState)(0);
	const [auditReport, setAuditReport] = (0, import_react.useState)(null);
	const [auditLoading, setAuditLoading] = (0, import_react.useState)(true);
	const [auditRunning, setAuditRunning] = (0, import_react.useState)(false);
	const [auditError, setAuditError] = (0, import_react.useState)(null);
	(0, import_react.useEffect)(() => {
		let cancelled = false;
		fetchDatasetAuditReport(dataset.dataset_id).then((r) => {
			if (!cancelled) setAuditReport(r);
		}).catch((e) => {
			if (!cancelled) setAuditError(e instanceof Error ? e.message : "Failed to load audit");
		}).finally(() => {
			if (!cancelled) setAuditLoading(false);
		});
		return () => {
			cancelled = true;
		};
	}, [dataset.dataset_id]);
	const handleRunAudit = async () => {
		setAuditRunning(true);
		setAuditError(null);
		try {
			setAuditReport(await runFullDatasetAudit(dataset.dataset_id));
		} catch (e) {
			setAuditError(e instanceof Error ? e.message : "Audit failed");
		} finally {
			setAuditRunning(false);
		}
	};
	const [showDeleteConfirm, setShowDeleteConfirm] = (0, import_react.useState)(false);
	const handleDelete = async () => {
		try {
			await deleteDataset(dataset.dataset_id);
			toast.success("Dataset deleted");
			onDeleted();
		} catch (e) {
			toast.error(e instanceof Error ? e.message : "Failed to delete dataset");
		}
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-4",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-center justify-between",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
					onClick: onBack,
					className: "text-sm text-muted-foreground hover:text-foreground transition-colors",
					children: "← Back to list"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
					variant: "destructive",
					size: "sm",
					onClick: () => setShowDeleteConfirm(true),
					className: "flex items-center gap-1.5",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Trash2, { className: "h-3.5 w-3.5" }), "Delete Dataset"]
				})]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Card, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(CardHeader, {
				className: "pb-3",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center justify-between",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(CardTitle, {
						className: "text-lg flex items-center gap-2",
						children: [dataset.name, dataset.is_champion && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("span", {
							className: "flex items-center gap-1 text-xs font-normal bg-yellow-500/15 text-yellow-700 dark:text-yellow-400 px-2 py-0.5 rounded-full border border-yellow-500/30",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Award, { className: "h-3 w-3" }), " Champion"]
						})]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "text-xs font-mono text-muted-foreground",
						children: dataset.dataset_id
					})]
				})
			}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(CardContent, {
				className: "space-y-6",
				children: [
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "grid grid-cols-2 md:grid-cols-4 gap-4",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-1",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
									className: "text-[10px] font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-1",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Image, { className: "h-3 w-3" }), " Total Images"]
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-xl font-semibold",
									children: dataset.total_images.toLocaleString()
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-1",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
									className: "text-[10px] font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-1",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Layers, { className: "h-3 w-3" }), " Classes"]
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-xl font-semibold",
									children: dataset.nc
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-1",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
									className: "text-[10px] font-mono uppercase tracking-wider text-muted-foreground flex items-center gap-1",
									children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Folder, { className: "h-3 w-3" }), " Root Path"]
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-xs font-mono truncate",
									title: dataset.root_path,
									children: dataset.root_path.split("/").slice(-2).join("/")
								})]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "space-y-1",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-[10px] font-mono uppercase tracking-wider text-muted-foreground",
									children: "Status"
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-sm font-medium capitalize",
									children: dataset.status
								})]
							})
						]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "space-y-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h4", {
							className: "text-sm font-semibold",
							children: "Splits"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
							className: "grid grid-cols-3 gap-2",
							children: dataset.splits.map((split) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
								className: "rounded-md border border-border bg-muted/30 p-3 text-center",
								children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-[10px] font-mono uppercase tracking-wider text-muted-foreground",
									children: split.name
								}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
									className: "text-lg font-semibold",
									children: split.image_count.toLocaleString()
								})]
							}, split.name))
						})]
					}),
					/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "space-y-2",
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h4", {
							className: "text-sm font-semibold",
							children: "Class Distribution"
						}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ClassDistributionBar, { distribution: dataset.class_distribution })]
					})
				]
			})] }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DatasetPrepPanel, {
				datasetId: dataset.dataset_id,
				datasetName: dataset.name,
				totalImages: dataset.total_images,
				onPrepComplete: () => setGalleryKey((k) => k + 1)
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LeakageAuditPanel, { datasetId: dataset.dataset_id }),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(DatasetAuditReport, {
				report: auditReport,
				loading: auditLoading,
				running: auditRunning,
				error: auditError,
				onRun: handleRunAudit
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ImportPanel, {
				datasetId: dataset.dataset_id,
				onImportComplete: () => setGalleryKey((k) => k + 1)
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "space-y-3",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h3", {
					className: "text-lg font-semibold flex items-center gap-2",
					children: [
						"Browse Images (",
						dataset.total_images.toLocaleString(),
						")"
					]
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ImageGallery, { datasetId: dataset.dataset_id }, galleryKey)]
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ConfirmDialog, {
				open: showDeleteConfirm,
				onOpenChange: setShowDeleteConfirm,
				title: "Delete dataset?",
				description: `'${dataset.name}' and all its images, labels, and configurations will be permanently deleted. This cannot be undone.`,
				confirmLabel: "Delete Dataset",
				onConfirm: handleDelete
			})
		]
	});
}
function ReviewToDatasetBuilder({ onBack }) {
	const [reviews, setReviews] = (0, import_react.useState)([]);
	const [loading, setLoading] = (0, import_react.useState)(true);
	const [error, setError] = (0, import_react.useState)(null);
	const [stage, setStage] = (0, import_react.useState)("stage2");
	const [versionName, setVersionName] = (0, import_react.useState)("");
	const [includeConfirmed, setIncludeConfirmed] = (0, import_react.useState)(true);
	const [includeRejected, setIncludeRejected] = (0, import_react.useState)(false);
	const [includeUnclear, setIncludeUnclear] = (0, import_react.useState)(false);
	const [notes, setNotes] = (0, import_react.useState)("");
	const [building, setBuilding] = (0, import_react.useState)(false);
	const [result, setResult] = (0, import_react.useState)(null);
	(0, import_react.useEffect)(() => {
		const load = async () => {
			try {
				setLoading(true);
				setReviews(await fetchAllReviews());
			} catch (err) {
				setError(err.message || "Failed to load reviews");
			} finally {
				setLoading(false);
			}
		};
		load();
	}, []);
	const counts = {
		confirm: reviews.filter((r) => r.operator_decision === "confirm").length,
		reject: reviews.filter((r) => r.operator_decision === "reject").length,
		reclassify: reviews.filter((r) => r.operator_decision === "reclassify").length,
		unclear: reviews.filter((r) => r.operator_decision === "unclear").length
	};
	const totalSelected = (includeConfirmed ? counts.confirm : 0) + (includeRejected ? counts.reject : 0) + (includeUnclear ? counts.unclear : 0);
	const canBuild = versionName.trim().length > 0 && totalSelected > 0;
	const handleBuild = async () => {
		setBuilding(true);
		setError(null);
		setResult(null);
		try {
			setResult(await buildDataset({
				stage,
				version_name: versionName.trim(),
				include_confirmed: includeConfirmed,
				include_rejected: includeRejected,
				include_unclear: includeUnclear,
				notes: notes.trim() || null
			}));
		} catch (err) {
			setError(err.message || "Build failed");
		} finally {
			setBuilding(false);
		}
	};
	if (loading) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "rounded-lg border border-border bg-card p-8 text-center text-muted-foreground",
		children: "Loading reviews..."
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "space-y-4",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("button", {
			onClick: onBack,
			className: "text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-1",
			children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(ArrowLeft, { className: "h-3.5 w-3.5" }), " Back to dataset list"]
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "rounded-lg border border-border bg-card p-6 space-y-6",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Hammer, { className: "h-5 w-5 text-primary" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
						className: "text-lg font-semibold",
						children: "Build Dataset from Review Flywheel"
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "grid grid-cols-2 sm:grid-cols-4 gap-3",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "rounded-md border border-green-500/30 bg-green-500/10 p-3 text-center",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-2xl font-bold text-green-600 dark:text-green-400",
								children: counts.confirm
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs text-muted-foreground",
								children: "Confirmed"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "rounded-md border border-red-500/30 bg-red-500/10 p-3 text-center",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-2xl font-bold text-red-600 dark:text-red-400",
								children: counts.reject
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs text-muted-foreground",
								children: "Rejected"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "rounded-md border border-blue-500/30 bg-blue-500/10 p-3 text-center",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-2xl font-bold text-blue-600 dark:text-blue-400",
								children: counts.reclassify
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs text-muted-foreground",
								children: "Reclassified"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "rounded-md border border-yellow-500/30 bg-yellow-500/10 p-3 text-center",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-2xl font-bold text-yellow-600 dark:text-yellow-400",
								children: counts.unclear
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
								className: "text-xs text-muted-foreground",
								children: "Unclear"
							})]
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-sm font-medium",
						children: "Include in dataset:"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
						className: "flex flex-wrap gap-4",
						children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
								className: "flex items-center gap-2 text-sm cursor-pointer",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
										type: "checkbox",
										checked: includeConfirmed,
										onChange: (e) => setIncludeConfirmed(e.target.checked),
										className: "rounded border-gray-300"
									}),
									"Confirmed (",
									counts.confirm,
									")"
								]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
								className: "flex items-center gap-2 text-sm cursor-pointer",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
										type: "checkbox",
										checked: includeRejected,
										onChange: (e) => setIncludeRejected(e.target.checked),
										className: "rounded border-gray-300"
									}),
									"Rejected (",
									counts.reject,
									")"
								]
							}),
							/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
								className: "flex items-center gap-2 text-sm cursor-pointer",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
										type: "checkbox",
										checked: includeUnclear,
										onChange: (e) => setIncludeUnclear(e.target.checked),
										className: "rounded border-gray-300"
									}),
									"Unclear (",
									counts.unclear,
									")"
								]
							})
						]
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "grid grid-cols-1 sm:grid-cols-3 gap-4",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-1.5",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
								className: "text-sm font-medium",
								children: "Stage"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("select", {
								value: stage,
								onChange: (e) => setStage(e.target.value),
								className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
										value: "stage1",
										children: "Stage 1 (SOD)"
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
										value: "stage2",
										children: "Stage 2 (7-class defect)"
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
										value: "stage3",
										children: "Stage 3 (21-class panel)"
									})
								]
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-1.5",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
								className: "text-sm font-medium",
								children: "Version Name"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
								type: "text",
								value: versionName,
								onChange: (e) => setVersionName(e.target.value),
								placeholder: "e.g. v2.1_flywheel",
								className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-1.5",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
								className: "text-sm font-medium",
								children: "Notes (optional)"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
								type: "text",
								value: notes,
								onChange: (e) => setNotes(e.target.value),
								placeholder: "Optional notes...",
								className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
							})]
						})
					]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center gap-3",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						onClick: handleBuild,
						disabled: !canBuild || building,
						title: !canBuild ? "Enter a version name and select at least one review type" : void 0,
						children: building ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-4 w-4 mr-1.5 animate-spin" }), "Building..."] }) : /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [
							/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Hammer, { className: "h-4 w-4 mr-1.5" }),
							"Build Dataset (",
							totalSelected,
							" items)"
						] })
					}), totalSelected === 0 && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", {
						className: "text-xs text-muted-foreground",
						children: "No items selected"
					})]
				}),
				error && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "rounded-md border border-red-500/30 bg-red-500/10 p-3 text-sm text-red-600 dark:text-red-400",
					children: ["Error: ", error]
				}),
				result && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "rounded-md border border-green-500/30 bg-green-500/10 p-3 text-sm space-y-1",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("p", {
						className: "font-medium text-green-700 dark:text-green-400",
						children: ["Dataset build registered: ", result.version_name]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
						className: "text-muted-foreground",
						children: result.message
					})]
				})
			]
		})]
	});
}
function NewDatasetDialog({ onClose, onCreated }) {
	const [activeTab, setActiveTab] = (0, import_react.useState)("empty");
	const [error, setError] = (0, import_react.useState)(null);
	const [versionName, setVersionName] = (0, import_react.useState)("");
	const [stage, setStage] = (0, import_react.useState)("stage2");
	const [notes, setNotes] = (0, import_react.useState)("");
	const [creating, setCreating] = (0, import_react.useState)(false);
	const [zipName, setZipName] = (0, import_react.useState)("");
	const [selectedFile, setSelectedFile] = (0, import_react.useState)(null);
	const [importing, setImporting] = (0, import_react.useState)(false);
	const [importResult, setImportResult] = (0, import_react.useState)(null);
	const handleCreateEmpty = async () => {
		if (!versionName.trim()) return;
		setCreating(true);
		setError(null);
		try {
			await createNewDataset(versionName.trim(), stage, notes || null);
			onCreated();
			onClose();
		} catch (err) {
			setError(err.message || "Failed to create dataset");
		} finally {
			setCreating(false);
		}
	};
	const handleImportZip = async () => {
		if (!zipName.trim() || !selectedFile) return;
		setImporting(true);
		setError(null);
		try {
			setImportResult(await importDatasetZip(selectedFile, zipName.trim()));
			onCreated();
		} catch (err) {
			setError(err.message || "Failed to import dataset");
		} finally {
			setImporting(false);
		}
	};
	const handleFileChange = (e) => {
		setSelectedFile(e.target.files?.[0] ?? null);
		setError(null);
	};
	if (importResult) return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "fixed inset-0 z-50 flex items-center justify-center bg-black/50",
		onClick: onClose,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "w-full max-w-lg space-y-4 rounded-lg border border-border bg-card p-6 shadow-xl",
			onClick: (e) => e.stopPropagation(),
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center justify-between",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("h3", {
						className: "text-lg font-semibold",
						children: ["Imported: ", importResult.dataset_id]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						onClick: onClose,
						className: "text-muted-foreground hover:text-foreground",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, { className: "h-5 w-5" })
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-sm text-muted-foreground",
					children: importResult.message
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SplitStructurePanel, { structure: importResult.structure }),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "flex justify-end",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
						onClick: onClose,
						children: "Done"
					})
				})
			]
		})
	});
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "fixed inset-0 z-50 flex items-center justify-center bg-black/50",
		onClick: onClose,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "w-full max-w-md space-y-4 rounded-lg border border-border bg-card p-6 shadow-xl",
			onClick: (e) => e.stopPropagation(),
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center justify-between",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h3", {
						className: "text-lg font-semibold",
						children: "New Dataset"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						onClick: onClose,
						className: "text-muted-foreground hover:text-foreground",
						children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(X, { className: "h-5 w-5" })
					})]
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex gap-2 border-b border-border pb-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						onClick: () => {
							setActiveTab("empty");
							setError(null);
						},
						className: `px-3 py-1.5 text-sm font-medium rounded-t-md transition-colors ${activeTab === "empty" ? "bg-muted text-foreground border-b-2 border-primary" : "text-muted-foreground hover:text-foreground"}`,
						children: "Empty Dataset"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						onClick: () => {
							setActiveTab("zip");
							setError(null);
						},
						className: `px-3 py-1.5 text-sm font-medium rounded-t-md transition-colors ${activeTab === "zip" ? "bg-muted text-foreground border-b-2 border-primary" : "text-muted-foreground hover:text-foreground"}`,
						children: "From YOLO ZIP"
					})]
				}),
				activeTab === "empty" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-3",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-1.5",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
								className: "text-sm font-medium",
								children: "Version Name"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
								type: "text",
								value: versionName,
								onChange: (e) => setVersionName(e.target.value),
								placeholder: "e.g. v4.0_expanded",
								className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-1.5",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
								className: "text-sm font-medium",
								children: "Stage"
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
										children: "Stage 2 (7-class defect)"
									}),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("option", {
										value: "stage3",
										children: "Stage 3 (21-class panel)"
									})
								]
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-1.5",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
								className: "text-sm font-medium",
								children: "Notes (optional)"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("textarea", {
								value: notes,
								onChange: (e) => setNotes(e.target.value),
								placeholder: "Purpose...",
								className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[60px]"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex justify-end gap-2 pt-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
								variant: "ghost",
								onClick: onClose,
								children: "Cancel"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
								onClick: handleCreateEmpty,
								disabled: !versionName.trim() || creating,
								children: creating ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-4 w-4 mr-1.5 animate-spin" }), " Creating..."] }) : "Create Empty"
							})]
						})
					]
				}),
				activeTab === "zip" && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "space-y-3",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-1.5",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
								className: "text-sm font-medium",
								children: "Version Name"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
								type: "text",
								value: zipName,
								onChange: (e) => setZipName(e.target.value),
								placeholder: "e.g. yolo_seg_clean_2200",
								className: "w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "space-y-1.5",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("label", {
								className: "text-sm font-medium",
								children: "Dataset ZIP"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("label", {
								className: "flex w-full cursor-pointer items-center justify-center gap-2 rounded-md border border-dashed border-input bg-background px-3 py-6 text-sm text-muted-foreground transition-colors hover:border-foreground/40",
								children: [
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Upload, { className: "h-4 w-4" }),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("span", { children: selectedFile ? selectedFile.name : "Click to select a .zip file" }),
									/* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
										type: "file",
										accept: ".zip",
										onChange: handleFileChange,
										className: "hidden"
									})
								]
							})]
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
							className: "flex justify-end gap-2 pt-2",
							children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
								variant: "ghost",
								onClick: onClose,
								children: "Cancel"
							}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Button, {
								onClick: handleImportZip,
								disabled: !zipName.trim() || !selectedFile || importing,
								children: importing ? /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(import_jsx_runtime.Fragment, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(LoaderCircle, { className: "h-4 w-4 mr-1.5 animate-spin" }), " Importing..."] }) : "Import ZIP"
							})]
						})
					]
				}),
				error && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-xs text-destructive",
					children: error
				})
			]
		})
	});
}
function DatasetsPage() {
	const [datasets, setDatasets] = (0, import_react.useState)([]);
	const [selectedDetail, setSelectedDetail] = (0, import_react.useState)(null);
	const [showNewDialog, setShowNewDialog] = (0, import_react.useState)(false);
	const [loading, setLoading] = (0, import_react.useState)(true);
	const [detailLoading, setDetailLoading] = (0, import_react.useState)(false);
	const [error, setError] = (0, import_react.useState)(null);
	const [viewMode, setViewMode] = (0, import_react.useState)("list");
	const loadDatasets = async () => {
		try {
			setLoading(true);
			setDatasets((await fetchDatasets()).datasets);
		} catch (err) {
			setError(err.message || "Failed to load datasets");
		} finally {
			setLoading(false);
		}
	};
	(0, import_react.useEffect)(() => {
		loadDatasets();
	}, []);
	const handleSelect = async (datasetId) => {
		try {
			setDetailLoading(true);
			setSelectedDetail(await fetchDatasetDetail(datasetId));
			setViewMode("detail");
		} catch (err) {
			setError(err.message || "Failed to load dataset detail");
		} finally {
			setDetailLoading(false);
		}
	};
	const handleBack = () => {
		setSelectedDetail(null);
		setViewMode("list");
	};
	const handleOpenBuilder = () => {
		setSelectedDetail(null);
		setViewMode("builder");
	};
	const handleBackFromBuilder = () => {
		setViewMode("list");
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "p-6 space-y-6",
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "flex items-start justify-between",
				children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h1", {
					className: "text-2xl font-semibold tracking-tight",
					children: "Dataset Management"
				}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "text-sm text-muted-foreground mt-1",
					children: "Engineer workspace. List dataset versions, audit leakage, and build new datasets from the data flywheel."
				})] }), !selectedDetail && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
						variant: "outline",
						size: "sm",
						onClick: handleOpenBuilder,
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Hammer, { className: "h-4 w-4 mr-1.5" }), "Build from Reviews"]
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Button, {
						size: "sm",
						onClick: () => setShowNewDialog(true),
						children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Plus, { className: "h-4 w-4 mr-1.5" }), "New Dataset"]
					})]
				})]
			}),
			loading && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "rounded-lg border border-border bg-card p-8 text-center text-muted-foreground",
				children: "Loading datasets..."
			}),
			error && /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
				className: "rounded-lg border border-border bg-card p-8 text-center text-destructive",
				children: ["Error: ", error]
			}),
			detailLoading && /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
				className: "rounded-lg border border-border bg-card p-8 text-center text-muted-foreground",
				children: "Loading dataset detail..."
			}),
			!loading && !error && !detailLoading && viewMode === "builder" && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(ReviewToDatasetBuilder, { onBack: handleBackFromBuilder }),
			!loading && !error && !detailLoading && viewMode === "detail" && selectedDetail && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DatasetDetailPanel, {
				dataset: selectedDetail,
				onBack: handleBack,
				onDeleted: () => {
					setSelectedDetail(null);
					setViewMode("list");
					loadDatasets();
				}
			}),
			!loading && !error && !detailLoading && !selectedDetail && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(DatasetListView, {
				datasets,
				onSelect: handleSelect
			}),
			showNewDialog && /* @__PURE__ */ (0, import_jsx_runtime.jsx)(NewDatasetDialog, {
				onClose: () => setShowNewDialog(false),
				onCreated: loadDatasets
			})
		]
	});
}
//#endregion
export { DatasetsPage as component };
