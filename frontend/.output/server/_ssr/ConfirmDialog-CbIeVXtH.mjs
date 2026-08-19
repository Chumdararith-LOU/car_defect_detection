import { j as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { a as AlertDialogDescription, c as AlertDialogTitle, i as AlertDialogContent, n as AlertDialogAction, o as AlertDialogFooter, r as AlertDialogCancel, s as AlertDialogHeader, t as AlertDialog } from "./alert-dialog-DsQ-Uqlb.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/ConfirmDialog-CbIeVXtH.js
var import_jsx_runtime = require_jsx_runtime();
function ConfirmDialog({ open, onOpenChange, title, description, confirmLabel = "Confirm", destructive = true, onConfirm }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialog, {
		open,
		onOpenChange,
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogContent, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogHeader, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialogTitle, { children: title }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialogDescription, { children: description })] }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(AlertDialogFooter, { children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialogCancel, { children: "Cancel" }), /* @__PURE__ */ (0, import_jsx_runtime.jsx)(AlertDialogAction, {
			onClick: onConfirm,
			className: destructive ? "bg-destructive text-destructive-foreground hover:bg-destructive/90" : void 0,
			children: confirmLabel
		})] })] })
	});
}
//#endregion
export { ConfirmDialog as t };
