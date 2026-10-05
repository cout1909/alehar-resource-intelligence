import type { ReactNode } from "react";

const labels: Record<string, string> = {
  VERIFIED: "Verified",
  REVIEW_REQUIRED: "Needs review",
  SOURCE_UNAVAILABLE: "Source unavailable",
  ERROR: "Error",
  PENDING: "Pending",
  APPROVED: "Approved",
  REJECTED: "Rejected",
  NOT_REQUIRED: "Not required",
  UNVERIFIED: "Not checked",
  success: "AI assisted",
  disabled: "AI off",
  not_configured: "Not configured",
  unavailable: "AI unavailable",
  skipped: "AI skipped",
};
export function Badge({ value }: { value: string }) {
  return (
    <span className={`badge badge-${value.toLowerCase()}`}>
      <span className="badge-dot" />
      {labels[value] || value}
    </span>
  );
}
export function Timestamp({ value }: { value: string | null }) {
  return (
    <time dateTime={value || undefined}>
      {value
        ? new Date(value).toLocaleString(undefined, {
            month: "short",
            day: "numeric",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
          })
        : "Not checked yet"}
    </time>
  );
}
export function ExternalLink({
  url,
  children = "Open source ↗",
}: {
  url: string | null;
  children?: ReactNode;
}) {
  if (!url || !/^https?:\/\//i.test(url))
    return <span className="muted">No source configured</span>;
  return (
    <a
      className="external"
      href={url}
      target="_blank"
      rel="noopener noreferrer"
    >
      {children}
    </a>
  );
}
export function LoadingState() {
  return (
    <div className="state" role="status">
      <span className="spinner" />
      Loading workspace data…
      <span className="caption">The free demo server may take about a minute to wake up.</span>
    </div>
  );
}
export function ErrorState({
  message,
  retry,
}: {
  message: string;
  retry?: () => void;
}) {
  return (
    <div className="notice error" role="alert">
      <span>{message}</span>
      {retry && (
        <button className="button small secondary" onClick={retry}>
          Retry
        </button>
      )}
    </div>
  );
}
export function EmptyState({
  title,
  children,
}: {
  title: string;
  children: ReactNode;
}) {
  return (
    <div className="state empty">
      <span className="empty-symbol">◇</span>
      <h3>{title}</h3>
      <p>{children}</p>
    </div>
  );
}
export function PageHeader({
  eyebrow,
  title,
  description,
  children,
}: {
  eyebrow: string;
  title: string;
  description: string;
  children?: ReactNode;
}) {
  return (
    <header className="page-header">
      <div>
        <div className="eyebrow">{eyebrow}</div>
        <h1>{title}</h1>
        <p>{description}</p>
      </div>
      <div className="header-actions">{children}</div>
    </header>
  );
}
export function Score({ value }: { value: number | undefined }) {
  return value === undefined ? (
    <span className="muted">—</span>
  ) : (
    <span
      className="score"
      title="Verification Confidence: rule-based identity score, not a statistically calibrated probability"
    >
      <strong>{value >= 85 ? "High" : value >= 50 ? "Medium" : "Low"}</strong>
      <span>Heuristic Score: {value}</span>
      <span>/100</span>
      <i style={{ width: `${value}%` }} />
    </span>
  );
}
export function Pagination({
  offset,
  count,
  onChange,
}: {
  offset: number;
  count: number;
  onChange: (value: number) => void;
}) {
  return (
    <div className="pagination">
      <span>
        Showing {count ? offset + 1 : 0}–{offset + count}
      </span>
      <div className="actions">
        <button
          className="button small secondary"
          disabled={!offset}
          onClick={() => onChange(Math.max(0, offset - 50))}
        >
          Previous
        </button>
        <button
          className="button small secondary"
          disabled={count < 50}
          onClick={() => onChange(offset + 50)}
        >
          Next
        </button>
      </div>
    </div>
  );
}
