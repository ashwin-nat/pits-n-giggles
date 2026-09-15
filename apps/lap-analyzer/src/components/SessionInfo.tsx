import { useSessions } from "../hooks/useSessions";

interface SessionInfoProps {
  sessionId: string;
}

// Read-only version/context metadata for the selected session. Shares the
// useSessions() cache with SessionSelector -- no extra fetch.
export function SessionInfo({ sessionId }: SessionInfoProps) {
  const { data: sessions } = useSessions();
  const session = sessions?.find((s) => s.id === sessionId);

  if (session === undefined) {
    return null;
  }

  return (
    <div className="rounded border border-slate-800 bg-slate-900/60 px-2 py-1 text-xs text-slate-400">
      <p>
        {session.formula} {session.gameYear} • Patch {session.gameVersion}
      </p>
      <p>App v{session.appVersion}</p>
    </div>
  );
}
