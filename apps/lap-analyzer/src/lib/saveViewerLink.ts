import type { Session } from "../types/api";

// Same-origin: the lap analyzer and the save viewer are both served by apps/web.
// Null for local files and older saves, which have no save viewer session.
export function saveViewerSessionUrl(session: Pick<Session, "sessionSlug"> | undefined): string | null {
  const slug = session?.sessionSlug;
  return slug ? `/save-viewer/sessions/${encodeURIComponent(slug)}?tab=lap-telemetry` : null;
}
