import { n as __toESM } from "../_runtime.mjs";
import { u as require_react } from "./@floating-ui/react-dom+[...].mjs";
import { j as require_jsx_runtime } from "./@radix-ui/react-alert-dialog+[...].mjs";
import { t as Primitive } from "./radix-ui__react-primitive.mjs";
//#region node_modules/@radix-ui/react-separator/dist/index.mjs
var import_react = /* @__PURE__ */ __toESM(require_react(), 1);
var import_jsx_runtime = require_jsx_runtime();
var NAME = "Separator";
var DEFAULT_ORIENTATION = "horizontal";
var ORIENTATIONS = ["horizontal", "vertical"];
var Separator = import_react.forwardRef((props, forwardedRef) => {
	const { decorative, orientation: orientationProp = DEFAULT_ORIENTATION, ...domProps } = props;
	const orientation = isValidOrientation(orientationProp) ? orientationProp : DEFAULT_ORIENTATION;
	const semanticProps = decorative ? { role: "none" } : {
		"aria-orientation": orientation === "vertical" ? orientation : void 0,
		role: "separator"
	};
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Primitive.div, {
		"data-orientation": orientation,
		...semanticProps,
		...domProps,
		ref: forwardedRef
	});
});
Separator.displayName = NAME;
function isValidOrientation(orientation) {
	return ORIENTATIONS.includes(orientation);
}
var Root = Separator;
//#endregion
export { Root as t };
