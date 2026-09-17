// Shared loading/error/disabled presentational states, reused across
// SessionSelector, DriverSelector, and LapSelector so the skeleton height,
// error wording, and disabled-placeholder markup stay in one place instead
// of drifting between three copy-pasted versions.

interface LoadingSkeletonProps {
  className?: string;
}

export function LoadingSkeleton({ className = "h-8" }: LoadingSkeletonProps) {
  return <div className={`${className} animate-pulse rounded bg-slate-800`} />;
}

interface ErrorMessageProps {
  what: string;
  error: unknown;
}

export function ErrorMessage({ what, error }: ErrorMessageProps) {
  return (
    <p className="text-xs text-red-400">
      Failed to load {what}: {error instanceof Error ? error.message : String(error)}
    </p>
  );
}

interface DisabledSelectProps {
  message: string;
}

export function DisabledSelect({ message }: DisabledSelectProps) {
  return (
    <select disabled className="rounded border border-slate-800 bg-slate-900 px-2 py-1 text-sm text-slate-600">
      <option>{message}</option>
    </select>
  );
}
