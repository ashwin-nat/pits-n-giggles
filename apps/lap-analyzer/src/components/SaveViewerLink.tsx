import { IS_BACKEND_MODE } from "../lib/appMode";
import { saveViewerSessionUrl } from "../lib/saveViewerLink";
import type { Session } from "../types/api";

interface SaveViewerLinkProps {
  session: Session | undefined;
  className?: string;
}

// Opens the session in the save viewer in a new tab. Renders nothing outside the Pits n' Giggles
// app (the standalone app has no save viewer) or when the session has no counterpart.
export function SaveViewerLink({ session, className = "" }: SaveViewerLinkProps) {
  const url = IS_BACKEND_MODE ? saveViewerSessionUrl(session) : null;
  if (url === null) {
    return null;
  }
  return (
    <a
      href={url}
      target="_blank"
      rel="noopener"
      title="Open this session in the save viewer"
      aria-label="Open this session in the save viewer"
      className={`rounded-md px-1.5 text-tone-500 hover:bg-tone-700 hover:text-tone-100 ${className}`}
    >
      ↗
    </a>
  );
}
