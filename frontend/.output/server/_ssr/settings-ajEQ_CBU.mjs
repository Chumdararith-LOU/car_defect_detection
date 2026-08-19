import { j as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { n as PageShell, t as PageHeader } from "./PageShell-CQ88Jn3b.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/settings-ajEQ_CBU.js
var import_jsx_runtime = require_jsx_runtime();
function SettingsPage() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(PageShell, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(PageHeader, {
		title: "Settings",
		subtitle: "Runtime and connection configuration"
	}), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
		className: "rounded-sm border border-border bg-card p-4 space-y-3",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
			className: "font-mono text-[10px] uppercase tracking-widest text-muted-foreground",
			children: "Backend URL"
		}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
			className: "font-mono text-xs text-foreground mt-1",
			children: "http://localhost:8010"
		})] }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
			className: "border-t border-border pt-3",
			children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
				className: "font-mono text-[10px] text-muted-foreground",
				children: "Runtime configuration and training settings — Coming in Phase 7"
			})
		})]
	})] });
}
//#endregion
export { SettingsPage as component };
