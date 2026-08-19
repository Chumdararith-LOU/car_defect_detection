import { n as __toESM } from "../_runtime.mjs";
import { B as listCheckpoints, U as listTaxonomies } from "./apiClient-ClfACpV5.mjs";
import { t as cn } from "./utils-C_uf36nf.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { j as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { a as SelectTrigger, i as SelectItem, n as Select, o as SelectValue, r as SelectContent } from "./label-CsQhRIhI.mjs";
import { i as Trigger, n as List, r as Root2, t as Content } from "../_libs/radix-ui__react-tabs.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/tabs-DtPBE-s0.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var Input = import_react.forwardRef(({ className, type, ...props }, ref) => {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("input", {
		type,
		className: cn("flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-base shadow-sm transition-colors file:border-0 file:bg-transparent file:text-sm file:font-medium file:text-foreground placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50 md:text-sm", className),
		ref,
		...props
	});
});
Input.displayName = "Input";
var NONE_VALUE$1 = "__none__";
function CheckpointPicker({ stage, value, onChange }) {
	const [checkpoints, setCheckpoints] = (0, import_react.useState)([]);
	const [loading, setLoading] = (0, import_react.useState)(true);
	(0, import_react.useEffect)(() => {
		let cancelled = false;
		setLoading(true);
		listCheckpoints(stage).then((res) => {
			if (!cancelled) setCheckpoints(res.checkpoints);
		}).catch(() => {
			if (!cancelled) setCheckpoints([]);
		}).finally(() => {
			if (!cancelled) setLoading(false);
		});
		return () => {
			cancelled = true;
		};
	}, [stage]);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
		value: value ?? NONE_VALUE$1,
		onValueChange: (v) => onChange(v === NONE_VALUE$1 ? null : v),
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, { placeholder: loading ? "Loading checkpoints..." : "Select a checkpoint" }) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectContent, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
			value: NONE_VALUE$1,
			children: "No checkpoint"
		}), checkpoints.map((c) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectItem, {
			value: c.id,
			children: [
				c.name,
				" · ",
				c.origin,
				" · nc=",
				c.nc
			]
		}, c.id))] })]
	});
}
var NONE_VALUE = "none";
function TaxonomyPicker({ stage, value, onChange }) {
	const [taxonomies, setTaxonomies] = (0, import_react.useState)([]);
	const [loading, setLoading] = (0, import_react.useState)(true);
	(0, import_react.useEffect)(() => {
		let cancelled = false;
		setLoading(true);
		listTaxonomies(stage).then((res) => {
			if (!cancelled) setTaxonomies(res.taxonomies);
		}).catch(() => {
			if (!cancelled) setTaxonomies([]);
		}).finally(() => {
			if (!cancelled) setLoading(false);
		});
		return () => {
			cancelled = true;
		};
	}, [stage]);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(Select, {
		value: value ?? NONE_VALUE,
		onValueChange: (v) => onChange(v === NONE_VALUE ? null : v),
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectTrigger, { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectValue, { placeholder: loading ? "Loading taxonomies..." : "Select a taxonomy" }) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectContent, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(SelectItem, {
			value: NONE_VALUE,
			children: "No taxonomy"
		}), taxonomies.map((t) => /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(SelectItem, {
			value: t.id,
			children: [
				t.name,
				" · ",
				t.stage,
				" · ",
				t.class_names.length,
				" classes"
			]
		}, t.id))] })]
	});
}
var Tabs = Root2;
var TabsList = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(List, {
	ref,
	className: cn("inline-flex h-9 items-center justify-center rounded-lg bg-muted p-1 text-muted-foreground", className),
	...props
}));
TabsList.displayName = List.displayName;
var TabsTrigger = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Trigger, {
	ref,
	className: cn("inline-flex items-center justify-center whitespace-nowrap rounded-md px-3 py-1 text-sm font-medium ring-offset-background cursor-pointer transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 disabled:cursor-not-allowed data-[state=active]:bg-background data-[state=active]:text-foreground data-[state=active]:shadow", className),
	...props
}));
TabsTrigger.displayName = Trigger.displayName;
var TabsContent = import_react.forwardRef(({ className, ...props }, ref) => /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Content, {
	ref,
	className: cn("mt-2 ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2", className),
	...props
}));
TabsContent.displayName = Content.displayName;
//#endregion
export { TabsList as a, TabsContent as i, Input as n, TabsTrigger as o, Tabs as r, TaxonomyPicker as s, CheckpointPicker as t };
