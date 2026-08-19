globalThis.__nitro_main__ = import.meta.url;
import { a as FastResponse, n as HTTPError, r as defineLazyEventHandler, t as H3Core } from "./_libs/h3+rou3+srvx.mjs";
import { t as HookableCore } from "./_libs/hookable.mjs";
//#region #nitro-vite-setup
function lazyService(loader) {
	let promise, mod;
	return { fetch(req) {
		if (mod) return mod.fetch(req);
		if (!promise) promise = loader().then((_mod) => mod = _mod.default || _mod);
		return promise.then((mod) => mod.fetch(req));
	} };
}
var services = { ["ssr"]: lazyService(() => import("./_ssr/ssr.mjs")) };
globalThis.__nitro_vite_envs__ = services;
//#endregion
//#region #nitro/virtual/public-assets-data
var public_assets_data_default = {
	"/assets/ConfirmDialog-Cc-A3Nzt.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"268-anfiqEx0y6ZGaBh09oj5T1VrYPM\"",
		"mtime": "2026-08-18T17:46:02.094Z",
		"size": 616,
		"path": "../public/assets/ConfirmDialog-Cc-A3Nzt.js"
	},
	"/assets/PageShell-BE1USFyh.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"265-EznreG06UPsWLr/IEO1hpIKKaCY\"",
		"mtime": "2026-08-18T17:46:02.094Z",
		"size": 613,
		"path": "../public/assets/PageShell-BE1USFyh.js"
	},
	"/assets/alert-dialog-C_LhxZ9A.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"2f55-txDaoxUia5clV6pY8BX3pWiY+XE\"",
		"mtime": "2026-08-18T17:46:02.095Z",
		"size": 12117,
		"path": "../public/assets/alert-dialog-C_LhxZ9A.js"
	},
	"/assets/apiClient-CIp_1L8W.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"38ab-Lf9vbRGS47vixQDG8a9xJ50RolA\"",
		"mtime": "2026-08-18T17:46:02.095Z",
		"size": 14507,
		"path": "../public/assets/apiClient-CIp_1L8W.js"
	},
	"/assets/badge-B3ErvOR4.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"3fd-hxMQNEylqkp4d08wdJLhMWEx3to\"",
		"mtime": "2026-08-18T17:46:02.097Z",
		"size": 1021,
		"path": "../public/assets/badge-B3ErvOR4.js"
	},
	"/assets/card-DqCNbcLd.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"56b-QcUl+CBBCjNswwl1vud1HOjZSmU\"",
		"mtime": "2026-08-18T17:46:02.097Z",
		"size": 1387,
		"path": "../public/assets/card-DqCNbcLd.js"
	},
	"/assets/circle-BeL8ZcGd.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"82-w/u3sW8T7byKLcuYZ7a1xnOgWn8\"",
		"mtime": "2026-08-18T17:46:02.097Z",
		"size": 130,
		"path": "../public/assets/circle-BeL8ZcGd.js"
	},
	"/assets/button-DzEvVh8B.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"f5a-5dA/pta69kiSvESfS5mME6tTYO0\"",
		"mtime": "2026-08-18T17:46:02.097Z",
		"size": 3930,
		"path": "../public/assets/button-DzEvVh8B.js"
	},
	"/assets/circle-check-B9HP-wY2.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"b2-0xQbmm4PPkNjofUBU9SK5cA+ztc\"",
		"mtime": "2026-08-18T17:46:02.097Z",
		"size": 178,
		"path": "../public/assets/circle-check-B9HP-wY2.js"
	},
	"/assets/constants-EuzElQPP.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"527-P3AYSsTXII4ao2gHCrfk1fxkjwA\"",
		"mtime": "2026-08-18T17:46:02.098Z",
		"size": 1319,
		"path": "../public/assets/constants-EuzElQPP.js"
	},
	"/assets/createLucideIcon-IrB5uTdA.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"4c7-aKEaaarqTpQIicvevx9u2WBpPmg\"",
		"mtime": "2026-08-18T17:46:02.098Z",
		"size": 1223,
		"path": "../public/assets/createLucideIcon-IrB5uTdA.js"
	},
	"/assets/demo-vehicle-QX9El2ws.jpg": {
		"type": "image/jpeg",
		"etag": "\"160cd-kdktoUBiJe5hw7oq7H4R6vKqI+c\"",
		"mtime": "2026-08-18T17:46:02.104Z",
		"size": 90317,
		"path": "../public/assets/demo-vehicle-QX9El2ws.jpg"
	},
	"/assets/datasets-DOqjkU4Y.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"e71c-cctNi9HCnXkUC5uDS0LLfPoeHso\"",
		"mtime": "2026-08-18T17:46:02.098Z",
		"size": 59164,
		"path": "../public/assets/datasets-DOqjkU4Y.js"
	},
	"/assets/dialog-1yAGcLw3.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"c26-twnO7USTp6VK98SRIjR5etPq9cY\"",
		"mtime": "2026-08-18T17:46:02.098Z",
		"size": 3110,
		"path": "../public/assets/dialog-1yAGcLw3.js"
	},
	"/assets/es2015-BSRFIXFc.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"6714-pDIFkXEcT0zqNGEwg8wk3xoDcus\"",
		"mtime": "2026-08-18T17:46:02.098Z",
		"size": 26388,
		"path": "../public/assets/es2015-BSRFIXFc.js"
	},
	"/assets/experiments-Cs_e1Q-E.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"1f8d-dZyPJ5/9SHFX8wcUZx5nwbUugvw\"",
		"mtime": "2026-08-18T17:46:02.099Z",
		"size": 8077,
		"path": "../public/assets/experiments-Cs_e1Q-E.js"
	},
	"/assets/flask-conical-BIvB6dQf.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"12e-fK5Xi9/edYC4MSN0eZJ3D9kOOYs\"",
		"mtime": "2026-08-18T17:46:02.099Z",
		"size": 302,
		"path": "../public/assets/flask-conical-BIvB6dQf.js"
	},
	"/assets/host-DzeVTITY.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"129a-2ddzHvs4vra1WTVtEa5OHqZuLxA\"",
		"mtime": "2026-08-18T17:46:02.100Z",
		"size": 4762,
		"path": "../public/assets/host-DzeVTITY.js"
	},
	"/assets/label-COPi5cqf.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"ce09-hRuHR+ATw0SmnRZQpN8+CyGBAvg\"",
		"mtime": "2026-08-18T17:46:02.100Z",
		"size": 52745,
		"path": "../public/assets/label-COPi5cqf.js"
	},
	"/assets/loader-circle-BSjp0R5z.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"90-AS60GytNf4g+wokvZZVpwv7u7LM\"",
		"mtime": "2026-08-18T17:46:02.100Z",
		"size": 144,
		"path": "../public/assets/loader-circle-BSjp0R5z.js"
	},
	"/assets/jsx-runtime-DGeXAQPT.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"3ab-mgnSm9dUpwL2+z7tKxJ2MsN0fOM\"",
		"mtime": "2026-08-18T17:46:02.100Z",
		"size": 939,
		"path": "../public/assets/jsx-runtime-DGeXAQPT.js"
	},
	"/assets/models-DG-DJF_d.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"a181-iN2Ut1rtTvVK96fzka27bO33vD8\"",
		"mtime": "2026-08-18T17:46:02.100Z",
		"size": 41345,
		"path": "../public/assets/models-DG-DJF_d.js"
	},
	"/assets/pencil-CwJf1hpQ.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"114-+omkVHAXHRTz/ABfChW77dLy0r4\"",
		"mtime": "2026-08-18T17:46:02.100Z",
		"size": 276,
		"path": "../public/assets/pencil-CwJf1hpQ.js"
	},
	"/assets/index-DB1M_WGI.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"5b5ce-tjX+Qz0tePWJQ3dYzIbwwCfO6ts\"",
		"mtime": "2026-08-18T17:46:02.093Z",
		"size": 374222,
		"path": "../public/assets/index-DB1M_WGI.js"
	},
	"/assets/react-vt4WmSOl.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"1d67-BPOYGZcDqVQtRgdRj1RwUcWBJwU\"",
		"mtime": "2026-08-18T17:46:02.100Z",
		"size": 7527,
		"path": "../public/assets/react-vt4WmSOl.js"
	},
	"/assets/refresh-cw-CVGipHy3.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"141-+8tiJMQfuT1DbjBHD0PAyqYrCLY\"",
		"mtime": "2026-08-18T17:46:02.100Z",
		"size": 321,
		"path": "../public/assets/refresh-cw-CVGipHy3.js"
	},
	"/assets/review-BCyelKII.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"259f-spn5jAdo7DFoqHsFm/cc4lTWcic\"",
		"mtime": "2026-08-18T17:46:02.101Z",
		"size": 9631,
		"path": "../public/assets/review-BCyelKII.js"
	},
	"/assets/settings-C5VP7k7c.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"339-FFWqVaVehYIPbg4vp8P9+ArPYfA\"",
		"mtime": "2026-08-18T17:46:02.103Z",
		"size": 825,
		"path": "../public/assets/settings-C5VP7k7c.js"
	},
	"/assets/routes-D-dmjQtf.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"122c7-/+Q5UQOHTU6JG0bGe9Cxp15MgA8\"",
		"mtime": "2026-08-18T17:46:02.101Z",
		"size": 74439,
		"path": "../public/assets/routes-D-dmjQtf.js"
	},
	"/assets/styles-suE2lvwG.css": {
		"type": "text/css; charset=utf-8",
		"etag": "\"186f1-KgpHtdJebW/Zsede1eon7TV2Gsw\"",
		"mtime": "2026-08-18T17:46:02.104Z",
		"size": 100081,
		"path": "../public/assets/styles-suE2lvwG.css"
	},
	"/assets/tabs-QpDp5oeJ.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"2185-xfjMHSI7LZ6O/2Y1uc/Q4HVYGUU\"",
		"mtime": "2026-08-18T17:46:02.103Z",
		"size": 8581,
		"path": "../public/assets/tabs-QpDp5oeJ.js"
	},
	"/assets/upload-D0HvvT0i.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"1f1-0vzc4Y/CtmnMi2kTsUZB4fViJrA\"",
		"mtime": "2026-08-18T17:46:02.103Z",
		"size": 497,
		"path": "../public/assets/upload-D0HvvT0i.js"
	},
	"/assets/training-Bv_9abY3.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"8f3f-daXNX9L4UNNoIDLV1vvAV6dvcow\"",
		"mtime": "2026-08-18T17:46:02.103Z",
		"size": 36671,
		"path": "../public/assets/training-Bv_9abY3.js"
	},
	"/assets/utils-DXalBF5w.js": {
		"type": "text/javascript; charset=utf-8",
		"etag": "\"672c-VPRy6wo6yijMxg/evFz+SmpriuM\"",
		"mtime": "2026-08-18T17:46:02.103Z",
		"size": 26412,
		"path": "../public/assets/utils-DXalBF5w.js"
	}
};
//#endregion
//#region #nitro/virtual/public-assets
var publicAssetBases = {};
function isPublicAssetURL(id = "") {
	if (public_assets_data_default[id]) return true;
	for (const base in publicAssetBases) if (id.startsWith(base)) return true;
	return false;
}
//#endregion
//#region node_modules/nitro/dist/runtime/internal/route-rules.mjs
var headers = ((m) => function headersRouteRule(event) {
	for (const [key, value] of Object.entries(m.options || {})) event.res.headers.set(key, value);
});
//#endregion
//#region #nitro/virtual/routing
var findRouteRules = /* @__PURE__ */ (() => {
	const $0 = [{
		name: "headers",
		route: "/assets/**",
		handler: headers,
		options: { "cache-control": "public, max-age=31536000, immutable" }
	}];
	return (m, p) => {
		let r = [];
		if (p.charCodeAt(p.length - 1) === 47) p = p.slice(0, -1) || "/";
		let s = p.split("/");
		if (s.length > 1) {
			if (s[1] === "assets") r.unshift({
				data: $0,
				params: { "_": s.slice(2).join("/") }
			});
		}
		return r;
	};
})();
var _lazy_PaRlG3 = defineLazyEventHandler(() => import("./_chunks/ssr-renderer.mjs"));
var findRoute = /* @__PURE__ */ (() => {
	const data = {
		route: "/**",
		handler: _lazy_PaRlG3
	};
	return ((_m, p) => {
		return {
			data,
			params: { "_": p.slice(1) }
		};
	});
})();
[].filter(Boolean);
//#endregion
//#region node_modules/nitro/dist/runtime/internal/error/prod.mjs
var errorHandler = (error, event) => {
	const res = defaultHandler(error, event);
	return new FastResponse(typeof res.body === "string" ? res.body : JSON.stringify(res.body, null, 2), res);
};
function defaultHandler(error, event) {
	const unhandled = error.unhandled ?? !HTTPError.isError(error);
	const { status = 500, statusText = "" } = unhandled ? {} : error;
	if (status === 404) {
		const url = event.url || new URL(event.req.url);
		const baseURL = "/";
		if (/^\/[^/]/.test(baseURL) && !url.pathname.startsWith(baseURL)) return {
			status: 302,
			headers: new Headers({ location: `${baseURL}${url.pathname.slice(1)}${url.search}` })
		};
	}
	const headers = new Headers(unhandled ? {} : error.headers);
	headers.set("content-type", "application/json; charset=utf-8");
	return {
		status,
		statusText,
		headers,
		body: {
			error: true,
			...unhandled ? {
				status,
				unhandled: true
			} : typeof error.toJSON === "function" ? error.toJSON() : {
				status,
				statusText,
				message: error.message
			}
		}
	};
}
//#endregion
//#region #nitro/virtual/error-handler
var errorHandlers = [errorHandler];
async function error_handler_default(error, event) {
	for (const handler of errorHandlers) try {
		const response = await handler(error, event, { defaultHandler });
		if (response) return response;
	} catch (error) {
		console.error(error);
	}
}
//#endregion
//#region #nitro/virtual/app
function createNitroApp() {
	const captureError = (error, errorCtx) => {
		if (errorCtx?.event) {
			const errors = errorCtx.event.req.context?.nitro?.errors;
			if (errors) errors.push({
				error,
				context: errorCtx
			});
		}
	};
	const h3App = createH3App({ onError(error, event) {
		return error_handler_default(error, event);
	} });
	let appHandler = (req) => {
		req.context ||= {};
		req.context.nitro = req.context.nitro || { errors: [] };
		return h3App.fetch(req);
	};
	return {
		fetch: appHandler,
		h3: h3App,
		hooks: void 0,
		captureError
	};
}
function createH3App(config) {
	const h3App = new H3Core(config);
	h3App["~findRoute"] = (event) => findRoute(event.req.method, event.url.pathname);
	h3App["~getMiddleware"] = (event, route) => {
		const pathname = event.url.pathname;
		const method = event.req.method;
		const middleware = [];
		const routeRules = getRouteRules(method, pathname);
		event.context.routeRules = routeRules?.routeRules;
		if (routeRules?.routeRuleMiddleware.length) middleware.push(...routeRules.routeRuleMiddleware);
		if (route?.data?.middleware?.length) middleware.push(...route.data.middleware);
		return middleware;
	};
	return h3App;
}
//#endregion
//#region node_modules/nitro/dist/runtime/internal/app.mjs
var APP_ID = "default";
function useNitroApp() {
	let instance = useNitroApp._instance;
	if (instance) return instance;
	instance = useNitroApp._instance = createNitroApp();
	globalThis.__nitro__ = globalThis.__nitro__ || {};
	globalThis.__nitro__[APP_ID] = instance;
	return instance;
}
function useNitroHooks() {
	const nitroApp = useNitroApp();
	const hooks = nitroApp.hooks;
	if (hooks) return hooks;
	return nitroApp.hooks = new HookableCore();
}
function getRouteRules(method, pathname) {
	const m = findRouteRules(method, pathname);
	if (!m?.length) return { routeRuleMiddleware: [] };
	const routeRules = {};
	for (const layer of m) for (const rule of layer.data) {
		const currentRule = routeRules[rule.name];
		if (currentRule) {
			if (rule.options === false) {
				delete routeRules[rule.name];
				continue;
			}
			if (typeof currentRule.options === "object" && typeof rule.options === "object") currentRule.options = {
				...currentRule.options,
				...rule.options
			};
			else currentRule.options = rule.options;
			currentRule.route = rule.route;
			currentRule.params = {
				...currentRule.params,
				...layer.params
			};
		} else if (rule.options !== false) routeRules[rule.name] = {
			...rule,
			params: layer.params
		};
	}
	const middleware = [];
	const orderedRules = Object.values(routeRules).sort((a, b) => (a.handler?.order || 0) - (b.handler?.order || 0));
	for (const rule of orderedRules) {
		if (rule.options === false || !rule.handler) continue;
		middleware.push(rule.handler(rule));
	}
	return {
		routeRules,
		routeRuleMiddleware: middleware
	};
}
//#endregion
//#region node_modules/nitro/dist/presets/cloudflare/runtime/_module-handler.mjs
function createHandler(hooks) {
	const nitroApp = useNitroApp();
	const nitroHooks = useNitroHooks();
	return {
		async fetch(request, env, context) {
			globalThis.__env__ = env;
			augmentReq(request, {
				env,
				context
			});
			const ctxExt = {};
			const url = new URL(request.url);
			if (hooks.fetch) {
				const res = await hooks.fetch(request, env, context, url, ctxExt);
				if (res) return res;
			}
			return await nitroApp.fetch(request);
		},
		scheduled(controller, env, context) {
			globalThis.__env__ = env;
			context.waitUntil(nitroHooks.callHook("cloudflare:scheduled", {
				controller,
				env,
				context
			}) || Promise.resolve());
		},
		email(message, env, context) {
			globalThis.__env__ = env;
			context.waitUntil(nitroHooks.callHook("cloudflare:email", {
				message,
				event: message,
				env,
				context
			}) || Promise.resolve());
		},
		queue(batch, env, context) {
			globalThis.__env__ = env;
			context.waitUntil(nitroHooks.callHook("cloudflare:queue", {
				batch,
				event: batch,
				env,
				context
			}) || Promise.resolve());
		},
		tail(traces, env, context) {
			globalThis.__env__ = env;
			context.waitUntil(nitroHooks.callHook("cloudflare:tail", {
				traces,
				env,
				context
			}) || Promise.resolve());
		},
		trace(traces, env, context) {
			globalThis.__env__ = env;
			context.waitUntil(nitroHooks.callHook("cloudflare:trace", {
				traces,
				env,
				context
			}) || Promise.resolve());
		}
	};
}
function augmentReq(cfReq, ctx) {
	const req = cfReq;
	req.ip = cfReq.headers.get("cf-connecting-ip") || void 0;
	req.runtime ??= { name: "cloudflare" };
	req.runtime.cloudflare = {
		...req.runtime.cloudflare,
		...ctx
	};
	req.waitUntil = ctx.context?.waitUntil.bind(ctx.context);
}
//#endregion
//#region node_modules/nitro/dist/presets/cloudflare/runtime/cloudflare-module.mjs
var cloudflare_module_default = createHandler({ fetch(cfRequest, env, context, url) {
	if (env.ASSETS && isPublicAssetURL(url.pathname)) return env.ASSETS.fetch(cfRequest);
} });
//#endregion
export { cloudflare_module_default as default };
