import { n as __toESM } from "../_runtime.mjs";
import { u as require_react } from "../_libs/@floating-ui/react-dom+[...].mjs";
import { j as require_jsx_runtime } from "../_libs/@radix-ui/react-alert-dialog+[...].mjs";
import { t as Toaster } from "../_libs/sonner.mjs";
import { c as HeadContent, d as Outlet, f as lazyRouteComponent, g as useRouter, h as Link, m as createRootRouteWithContext, p as createFileRoute, s as Scripts, u as createRouter } from "../_libs/@tanstack/react-router+[...].mjs";
import { t as QueryClient } from "../_libs/tanstack__query-core.mjs";
import { t as QueryClientProvider } from "../_libs/tanstack__react-query.mjs";
//#region node_modules/.nitro/vite/services/ssr/assets/router-BX3m5GoD.js
var import_react = /* @__PURE__ */ __toESM(require_react());
var import_jsx_runtime = require_jsx_runtime();
var styles_default = "/assets/styles-suE2lvwG.css";
function reportLovableError(error, context = {}) {
	if (typeof window === "undefined") return;
	window.__lovableEvents?.captureException?.(error, {
		source: "react_error_boundary",
		route: window.location.pathname,
		...context
	}, {
		mechanism: "react_error_boundary",
		handled: false,
		severity: "error"
	});
}
var Toaster$1 = ({ ...props }) => {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Toaster, {
		className: "toaster group",
		toastOptions: { classNames: {
			toast: "group toast group-[.toaster]:bg-background group-[.toaster]:text-foreground group-[.toaster]:border-border group-[.toaster]:shadow-lg",
			description: "group-[.toast]:text-muted-foreground",
			actionButton: "group-[.toast]:bg-primary group-[.toast]:text-primary-foreground",
			cancelButton: "group-[.toast]:bg-muted group-[.toast]:text-muted-foreground"
		} },
		...props
	});
};
function NotFoundComponent() {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "flex min-h-screen items-center justify-center bg-background px-4",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "max-w-md text-center",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h1", {
					className: "text-7xl font-bold text-foreground",
					children: "404"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h2", {
					className: "mt-4 text-xl font-semibold text-foreground",
					children: "Page not found"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "mt-2 text-sm text-muted-foreground",
					children: "The page you're looking for doesn't exist or has been moved."
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
					className: "mt-6",
					children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
						to: "/",
						className: "inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90",
						children: "Go home"
					})
				})
			]
		})
	});
}
function ErrorComponent({ error, reset }) {
	console.error(error);
	const router = useRouter();
	(0, import_react.useEffect)(() => {
		reportLovableError(error, { boundary: "tanstack_root_error_component" });
	}, [error]);
	return /* @__PURE__ */ (0, import_jsx_runtime.jsx)("div", {
		className: "flex min-h-screen items-center justify-center bg-background px-4",
		children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
			className: "max-w-md text-center",
			children: [
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("h1", {
					className: "text-xl font-semibold tracking-tight text-foreground",
					children: "This page didn't load"
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsx)("p", {
					className: "mt-2 text-sm text-muted-foreground",
					children: "Something went wrong on our end. You can try refreshing or head back home."
				}),
				/* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "mt-6 flex flex-wrap justify-center gap-2",
					children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("button", {
						onClick: () => {
							router.invalidate();
							reset();
						},
						className: "inline-flex items-center justify-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90",
						children: "Try again"
					}), /* @__PURE__ */ (0, import_jsx_runtime.jsx)("a", {
						href: "/",
						className: "inline-flex items-center justify-center rounded-md border border-input bg-background px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-accent",
						children: "Go home"
					})]
				})
			]
		})
	});
}
var Route$8 = createRootRouteWithContext()({
	head: () => ({
		meta: [
			{ charSet: "utf-8" },
			{
				name: "viewport",
				content: "width=device-width, initial-scale=1"
			},
			{ title: "AI Exterior Defect Inspection Dashboard" },
			{
				name: "description",
				content: "Multi-stage AI pipeline for component-aware automotive exterior defect detection."
			},
			{
				name: "author",
				content: "AI Farm Robotics"
			},
			{
				property: "og:title",
				content: "AI Exterior Defect Inspection Dashboard"
			},
			{
				property: "og:description",
				content: "Pre-screen, tiled detection, and component context mapping for automotive QA."
			},
			{
				property: "og:type",
				content: "website"
			},
			{
				name: "twitter:card",
				content: "summary_large_image"
			}
		],
		links: [
			{
				rel: "stylesheet",
				href: styles_default
			},
			{
				rel: "icon",
				href: "/favicon.ico",
				type: "image/x-icon"
			},
			{
				rel: "stylesheet",
				href: "https://fonts.googleapis.com/css2?family=Chakra+Petch:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap"
			}
		]
	}),
	shellComponent: RootShell,
	component: RootComponent,
	notFoundComponent: NotFoundComponent,
	errorComponent: ErrorComponent
});
function RootShell({ children }) {
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("html", {
		lang: "en",
		children: [/* @__PURE__ */ (0, import_jsx_runtime.jsx)("head", { children: /* @__PURE__ */ (0, import_jsx_runtime.jsx)(HeadContent, {}) }), /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("body", { children: [children, /* @__PURE__ */ (0, import_jsx_runtime.jsx)(Scripts, {})] })]
	});
}
function RootComponent() {
	const { queryClient } = Route$8.useRouteContext();
	return /* @__PURE__ */ (0, import_jsx_runtime.jsxs)(QueryClientProvider, {
		client: queryClient,
		children: [
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)("nav", {
				className: "border-b border-border bg-card",
				children: /* @__PURE__ */ (0, import_jsx_runtime.jsxs)("div", {
					className: "flex items-center gap-0",
					children: [
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
							to: "/",
							className: "px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-muted-foreground border-b-2 border-transparent hover:text-foreground transition-colors",
							activeProps: { className: "px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-foreground border-b-2 border-primary transition-colors" },
							children: "Inspection"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
							to: "/host",
							className: "px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-muted-foreground border-b-2 border-transparent hover:text-foreground transition-colors",
							activeProps: { className: "px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-foreground border-b-2 border-primary transition-colors" },
							children: "Host System"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
							to: "/review",
							className: "px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-muted-foreground border-b-2 border-transparent hover:text-foreground transition-colors",
							activeProps: { className: "px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-foreground border-b-2 border-primary transition-colors" },
							children: "Review Queue"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
							to: "/datasets",
							activeProps: { className: "text-primary font-semibold" },
							inactiveProps: { className: "text-muted-foreground hover:text-foreground" },
							className: "text-sm transition-colors",
							children: "Datasets"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
							to: "/experiments",
							className: "px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors",
							activeProps: { className: "px-3 py-2 rounded-md text-sm font-medium bg-primary/10 text-primary" },
							children: "Experiments"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
							to: "/models",
							className: "px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors",
							activeProps: { className: "px-3 py-2 rounded-md text-sm font-medium bg-primary/10 text-primary" },
							children: "Models"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
							to: "/training",
							className: "px-3 py-2 rounded-md text-sm font-medium text-muted-foreground hover:text-foreground hover:bg-muted transition-colors",
							activeProps: { className: "px-3 py-2 rounded-md text-sm font-medium bg-primary/10 text-primary" },
							children: "Training"
						}),
						/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Link, {
							to: "/settings",
							className: "px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-muted-foreground border-b-2 border-transparent hover:text-foreground transition-colors",
							activeProps: { className: "px-4 py-3 font-mono text-[10px] uppercase tracking-widest text-foreground border-b-2 border-primary transition-colors" },
							children: "Settings"
						})
					]
				})
			}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Outlet, {}),
			/* @__PURE__ */ (0, import_jsx_runtime.jsx)(Toaster$1, {})
		]
	});
}
var $$splitComponentImporter$7 = () => import("./training-DyCiS9ER.mjs");
var Route$7 = createFileRoute("/training")({ component: lazyRouteComponent($$splitComponentImporter$7, "component") });
var $$splitComponentImporter$6 = () => import("./settings-ajEQ_CBU.mjs");
var Route$6 = createFileRoute("/settings")({ component: lazyRouteComponent($$splitComponentImporter$6, "component") });
var $$splitComponentImporter$5 = () => import("./review-BLfOj5pX.mjs");
var Route$5 = createFileRoute("/review")({ component: lazyRouteComponent($$splitComponentImporter$5, "component") });
var $$splitComponentImporter$4 = () => import("./models-BHVMjZLY.mjs");
var Route$4 = createFileRoute("/models")({ component: lazyRouteComponent($$splitComponentImporter$4, "component") });
var $$splitComponentImporter$3 = () => import("./host-CvKyd4Z0.mjs");
var Route$3 = createFileRoute("/host")({ component: lazyRouteComponent($$splitComponentImporter$3, "component") });
var $$splitComponentImporter$2 = () => import("./experiments-rMCI0Uv3.mjs");
var Route$2 = createFileRoute("/experiments")({ component: lazyRouteComponent($$splitComponentImporter$2, "component") });
var $$splitComponentImporter$1 = () => import("./datasets-D9onRmQO.mjs");
var Route$1 = createFileRoute("/datasets")({ component: lazyRouteComponent($$splitComponentImporter$1, "component") });
var $$splitComponentImporter = () => import("./routes-CzbL3VB9.mjs");
var Route = createFileRoute("/")({
	head: () => ({ meta: [
		{ title: "AI Exterior Defect Inspection Dashboard" },
		{
			name: "description",
			content: "Multi-stage AI pipeline for component-aware automotive exterior defect detection and industrial quality inspection."
		},
		{
			property: "og:title",
			content: "AI Exterior Defect Inspection Dashboard"
		},
		{
			property: "og:description",
			content: "Pre-screen, tiled detection, and component context mapping for automotive quality inspection."
		}
	] }),
	component: lazyRouteComponent($$splitComponentImporter, "component")
});
var TrainingRoute = Route$7.update({
	id: "/training",
	path: "/training",
	getParentRoute: () => Route$8
});
var SettingsRoute = Route$6.update({
	id: "/settings",
	path: "/settings",
	getParentRoute: () => Route$8
});
var ReviewRoute = Route$5.update({
	id: "/review",
	path: "/review",
	getParentRoute: () => Route$8
});
var ModelsRoute = Route$4.update({
	id: "/models",
	path: "/models",
	getParentRoute: () => Route$8
});
var HostRoute = Route$3.update({
	id: "/host",
	path: "/host",
	getParentRoute: () => Route$8
});
var ExperimentsRoute = Route$2.update({
	id: "/experiments",
	path: "/experiments",
	getParentRoute: () => Route$8
});
var DatasetsRoute = Route$1.update({
	id: "/datasets",
	path: "/datasets",
	getParentRoute: () => Route$8
});
var rootRouteChildren = {
	IndexRoute: Route.update({
		id: "/",
		path: "/",
		getParentRoute: () => Route$8
	}),
	DatasetsRoute,
	ExperimentsRoute,
	HostRoute,
	ModelsRoute,
	ReviewRoute,
	SettingsRoute,
	TrainingRoute
};
var routeTree = Route$8._addFileChildren(rootRouteChildren)._addFileTypes();
var getRouter = () => {
	return createRouter({
		routeTree,
		context: { queryClient: new QueryClient() },
		scrollRestoration: true,
		defaultPreloadStaleTime: 0
	});
};
//#endregion
export { getRouter };
