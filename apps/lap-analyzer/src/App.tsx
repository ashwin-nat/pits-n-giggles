import { useEffect, useState, type ChangeEvent } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ProviderContext, type ActiveProvider } from "./providers/ProviderContext";
import { LocalFileProvider } from "./providers/LocalFileProvider";
import { RemoteApiProvider } from "./providers/RemoteApiProvider";
import { Layout } from "./components/layout/Layout";
import { ChartArea } from "./components/chart/ChartArea";
import { useTelemetryStore } from "./store/telemetryStore";

const queryClient = new QueryClient();

// apps/web always mounts this SPA at /lap-analyzer/ (see render_lap_analyzer_index
// in lap_analyzer_routes.py); a standalone `pnpm dev`/local dist/ is always served
// from "/". Reading the live URL avoids depending on a build-time constant (Vite's
// `base`, see vite.config.ts) staying in sync with how the page actually got here.
const IS_BACKEND_MODE = window.location.pathname.startsWith("/lap-analyzer/");

export function App() {
  const [active, setActive] = useState<ActiveProvider | null>(null);
  const resetSelection = useTelemetryStore((state) => state.reset);

  function switchProvider(provider: ActiveProvider["provider"]) {
    // Every distance/index in the current selection state is scoped to the
    // provider it came from -- a new provider means a different session/
    // driver/lap manifest, so stale primary/reference/viewport/activeSection
    // must be cleared, not just replaced with a new provider underneath them.
    resetSelection();
    console.log(`Lap Analyzer: switching to ${provider.constructor.name}`);
    setActive({ provider, id: crypto.randomUUID() });
  }

  // Backend mode has exactly one provider -- select it automatically instead
  // of making the user click a button that was only ever there for Phase 6
  // manual testing.
  useEffect(() => {
    if (IS_BACKEND_MODE) {
      switchProvider(new RemoteApiProvider());
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    // Reset so selecting the same path again still fires a change event --
    // otherwise retrying after a parse failure, or reloading a regenerated
    // fixture with the same name, silently does nothing.
    event.currentTarget.value = "";
    if (file === undefined) {
      return;
    }
    switchProvider(new LocalFileProvider(file));
  }

  return (
    <QueryClientProvider client={queryClient}>
      <ProviderContext.Provider value={active}>
        {/* h-screen only, no w-screen -- the shared nav sidebar (injected server-side,
            see render_lap_analyzer_index) reserves its width via `body.png-has-sidebar`'s
            padding-left; w-screen (100vw) would ignore that padding and render this div
            underneath the fixed sidebar instead of beside it. Same reasoning as
            f1-save-viewer's own root layout, which only sets h-screen for the same reason. */}
        <div className="flex h-screen flex-col bg-slate-950">
          <header className="flex items-center gap-3 border-b border-slate-800 bg-slate-900 px-4 py-2">
            <p className="text-sm font-semibold text-slate-100">Lap Analyzer</p>
            {/* Standalone/dev mode only -- backend mode has no local file to browse for,
                it always talks to RemoteApiProvider (see IS_BACKEND_MODE above). */}
            {!IS_BACKEND_MODE && (
              <input
                type="file"
                accept=".pngt"
                onChange={handleFileChange}
                className="cursor-pointer text-xs text-slate-400 file:mr-3 file:cursor-pointer file:rounded file:border-0 file:bg-slate-700 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-slate-100 file:hover:bg-slate-600"
              />
            )}
          </header>
          <div className="min-h-0 flex-1">
            <Layout>
              <ChartArea />
            </Layout>
          </div>
        </div>
      </ProviderContext.Provider>
    </QueryClientProvider>
  );
}
