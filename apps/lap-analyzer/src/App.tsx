import { useState, type ChangeEvent } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ProviderContext, type ActiveProvider } from "./providers/ProviderContext";
import { LocalFileProvider } from "./providers/LocalFileProvider";
import { Layout } from "./components/layout/Layout";
import { useTelemetryStore } from "./store/telemetryStore";

const queryClient = new QueryClient();

export function App() {
  const [active, setActive] = useState<ActiveProvider | null>(null);
  const resetSelection = useTelemetryStore((state) => state.reset);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file === undefined) {
      return;
    }
    // A new file's sessionId/driverIndex/lapNumber share nothing with the
    // previous one's -- drop any selection left over from it rather than
    // leaving the sidebar cascade pointing at now-meaningless ids.
    resetSelection();
    setActive({ provider: new LocalFileProvider(file), id: crypto.randomUUID() });
  }

  return (
    <QueryClientProvider client={queryClient}>
      <ProviderContext.Provider value={active}>
        <div className="flex h-screen w-screen flex-col bg-slate-950">
          <header className="flex items-center gap-3 border-b border-slate-800 bg-slate-900 px-4 py-2">
            <p className="text-sm font-semibold text-slate-100">Lap Analyzer</p>
            <input type="file" accept=".pngt" onChange={handleFileChange} className="text-xs text-slate-300" />
          </header>
          <div className="min-h-0 flex-1">
            <Layout>
              <div className="p-4 text-sm text-slate-500">Chart area -- Phase 5</div>
            </Layout>
          </div>
        </div>
      </ProviderContext.Provider>
    </QueryClientProvider>
  );
}
