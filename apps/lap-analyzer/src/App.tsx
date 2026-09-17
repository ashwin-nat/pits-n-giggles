import { useState, type ChangeEvent } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ProviderContext, type ActiveProvider } from "./providers/ProviderContext";
import { LocalFileProvider } from "./providers/LocalFileProvider";
import { Layout } from "./components/layout/Layout";
import { ChartArea } from "./components/chart/ChartArea";
import { useTelemetryStore } from "./store/telemetryStore";

const queryClient = new QueryClient();

export function App() {
  const [active, setActive] = useState<ActiveProvider | null>(null);
  const resetSelection = useTelemetryStore((state) => state.reset);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    // Reset so selecting the same path again still fires a change event --
    // otherwise retrying after a parse failure, or reloading a regenerated
    // fixture with the same name, silently does nothing.
    event.currentTarget.value = "";
    if (file === undefined) {
      return;
    }
    // Every distance/index in the current selection state is scoped to the
    // provider it came from -- a new file means a different session/driver/
    // lap manifest, so stale primary/reference/viewport/activeSection must
    // be cleared, not just replaced with a new provider underneath them.
    resetSelection();
    setActive({ provider: new LocalFileProvider(file), id: crypto.randomUUID() });
  }

  return (
    <QueryClientProvider client={queryClient}>
      <ProviderContext.Provider value={active}>
        <div className="flex h-screen w-screen flex-col bg-slate-950">
          <header className="flex items-center gap-3 border-b border-slate-800 bg-slate-900 px-4 py-2">
            <p className="text-sm font-semibold text-slate-100">Lap Analyzer</p>
            <input
              type="file"
              accept=".pngt"
              onChange={handleFileChange}
              className="cursor-pointer text-xs text-slate-400 file:mr-3 file:cursor-pointer file:rounded file:border-0 file:bg-slate-700 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-slate-100 file:hover:bg-slate-600"
            />
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
