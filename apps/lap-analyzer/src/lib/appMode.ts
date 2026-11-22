// apps/web always mounts this SPA at /lap-analyzer/ (see render_lap_analyzer_index
// in lap_analyzer_routes.py); a standalone `pnpm dev`/local dist/ is always served
// from "/". Reading the live URL avoids depending on a build-time constant (Vite's
// `base`, see vite.config.ts) staying in sync with how the page actually got here.
export const IS_BACKEND_MODE = window.location.pathname.startsWith("/lap-analyzer/");
