import { useEffect, useState, type ChangeEvent } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ProviderContext, type ActiveProvider } from "./providers/ProviderContext";
import { LocalFileProvider } from "./providers/LocalFileProvider";
import { PngtError } from "./lib/pngtErrors";
import { useSessions } from "./hooks/useSessions";

// TODO(phase-3): temporary init-tracing logs, remove once the app is stable
// and there's real UI feedback (loading spinners, error banners) instead.
const queryClient = new QueryClient();
console.log("[lap-analyzer] QueryClient created");

function SessionList() {
  const { data: sessions, isLoading, error } = useSessions();

  useEffect(() => {
    console.log("[lap-analyzer] useSessions state:", {
      isLoading,
      error: error ? String(error) : null,
      sessionCount: sessions?.length ?? null,
    });
  }, [isLoading, error, sessions]);

  if (isLoading) {
    return <p className="text-slate-600">Loading sessions...</p>;
  }
  if (error) {
    const message = error instanceof PngtError ? error.message : String(error);
    return <p className="text-red-600">Failed to parse file: {message}</p>;
  }
  if (sessions === undefined || sessions.length === 0) {
    return <p className="text-slate-600">No sessions found.</p>;
  }

  return (
    <ul className="list-disc pl-6">
      {sessions.map((session) => (
        <li key={session.id}>
          {session.name} -- {session.trackName} ({session.type})
        </li>
      ))}
    </ul>
  );
}

export function App() {
  const [active, setActive] = useState<ActiveProvider | null>(null);

  useEffect(() => {
    console.log("[lap-analyzer] App mounted");
  }, []);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (file === undefined) {
      return;
    }
    console.log(`[lap-analyzer] file selected: ${file.name} (${file.size} bytes)`);
    const id = crypto.randomUUID();
    setActive({ provider: new LocalFileProvider(file), id });
    console.log(`[lap-analyzer] LocalFileProvider created, id=${id}`);
  }

  return (
    <QueryClientProvider client={queryClient}>
      <ProviderContext.Provider value={active}>
        <div className="p-4">
          <p className="text-lg font-semibold text-slate-900">Lap Analyzer</p>
          <input type="file" accept=".pngt" onChange={handleFileChange} className="mt-2" />
          <div className="mt-4">{active !== null && <SessionList />}</div>
        </div>
      </ProviderContext.Provider>
    </QueryClientProvider>
  );
}
