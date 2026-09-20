import { useState, type ChangeEvent } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ProviderContext, type ActiveProvider } from "./providers/ProviderContext";
import { LocalFileProvider } from "./providers/LocalFileProvider";
import { RemoteApiProvider } from "./providers/RemoteApiProvider";
import { Layout } from "./components/layout/Layout";
import { ChartArea } from "./components/chart/ChartArea";
import { useTelemetryStore } from "./store/telemetryStore";

const queryClient = new QueryClient();

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

  function handleUseBackend() {
    switchProvider(new RemoteApiProvider());
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
            <input
              type="file"
              accept=".pngt"
              onChange={handleFileChange}
              className="cursor-pointer text-xs text-slate-400 file:mr-3 file:cursor-pointer file:rounded file:border-0 file:bg-slate-700 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-slate-100 file:hover:bg-slate-600"
            />
            {/* RemoteApiProvider toggle -- Phase 6 manual end-to-end testing against a
                real backend (see /lap-analyzer/api/v1/*) alongside the existing local-file
                path. Not gated behind a dev-only flag: both providers implement the same
                interface, so there is no production-safety reason to hide this. */}
            <button
              type="button"
              onClick={handleUseBackend}
              className="cursor-pointer rounded border-0 bg-slate-700 px-3 py-1.5 text-xs font-medium text-slate-100 hover:bg-slate-600"
            >
              Use Backend
            </button>
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
