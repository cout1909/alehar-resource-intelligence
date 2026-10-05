import { useWorkspace } from "../hooks/useWorkspace";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useResource } from "../hooks/useResource";
import ResultsTable from "../components/ResultsTable";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  Timestamp,
} from "../components/ui";

export default function Dashboard() {
  const { mutationsDisabled } = useWorkspace();
  const resource = useResource(async () => {
    const [summary, lenders, results, system, latest] = await Promise.all([
      api.summary(),
      api.lenders(),
      api.history("?limit=6"),
      api.system(),
      api.latest(),
    ]);
    return { summary, lenders: lenders.lenders, results, system, latest };
  });
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const verify = async () => {
    setBusy(true);
    setError("");
    setMessage("");
    try {
      const result = await api.verifyAll();
      setMessage(
        `Checked ${result.total} lenders: ${result.verified} verified, ${result.review_required} need review, ${result.source_unavailable} unavailable, ${result.errors} errors.`,
      );
      resource.reload();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(false);
    }
  };
  const data = resource.data;
  return (
    <>
      <PageHeader
        eyebrow="OVERVIEW"
        title="Alehar Resource Intelligence"
        description="AI-assisted monitoring and verification for public business-resource data."
      >
        <button
          className="button"
          onClick={verify}
          disabled={
            mutationsDisabled ||
            busy ||
            resource.loading ||
            !!resource.error ||
            data?.system.verification_running
          }
        >
          {busy ? "Verifying lenders…" : "↻ Verify All"}
        </button>
      </PageHeader>
      {error && <ErrorState message={error} />}
      {message && (
        <div className="notice success" role="status">
          {message}
        </div>
      )}
      {busy && (
        <div className="notice" role="status">
          Checking sources sequentially. This may take several minutes; keep
          this page open.
        </div>
      )}
      {resource.loading ? (
        <LoadingState />
      ) : resource.error ? (
        <ErrorState message={resource.error} retry={resource.reload} />
      ) : (
        data && (
          <>
            <div className="summary-grid">
              {[
                [
                  "Monitored Records",
                  data.summary.total_lenders,
                  "Curated public-source records",
                  "neutral",
                ],
                [
                  "Verified",
                  data.summary.verified,
                  "Basic source identity consistent",
                  "green",
                ],
                [
                  "Needs Review",
                  data.summary.review_required,
                  "Possible concerns to examine",
                  "amber",
                ],
                [
                  "Source Unavailable",
                  data.summary.source_unavailable,
                  "Could not independently verify",
                  "slate",
                ],
                [
                  "Pending Reviews",
                  data.summary.pending_reviews,
                  "Findings awaiting a decision",
                  "amber",
                ],
              ].map(([label, value, caption, color]) => (
                <article className={`summary-card ${color}`} key={label}>
                  <span>{label}</span>
                  <strong>{value}</strong>
                  <small>{caption}</small>
                </article>
              ))}
            </div>
            <div className="overview-grid">
              <section className="panel review-callout">
                <div>
                  <div className="eyebrow">Records Requiring Attention</div>
                  <h2>
                    {data.summary.pending_reviews}{" "}
                    {data.summary.pending_reviews === 1
                      ? "finding awaits"
                      : "findings await"}{" "}
                    review
                  </h2>
                  <p>
                    Examine source evidence and record a considered decision.
                    <br />
                    Lender records are never changed automatically.
                  </p>
                  <Link to="/reviews" className="button secondary">
                    Open review queue <span>→</span>
                  </Link>
                  <ul className="attention-list">
                    {data.latest
                      .filter((result) => result.status !== "VERIFIED")
                      .slice(0, 3)
                      .map((result) => (
                        <li key={result.id}>
                          <Link
                            to={`/lenders/${result.lender_id}?result=${result.id}`}
                          >
                            {data.lenders.find(
                              (lender) => lender.id === result.lender_id,
                            )?.name || "View record"}
                          </Link>
                          <span>{result.detected_changes[0]?.message}</span>
                        </li>
                      ))}
                  </ul>
                </div>
                <div className="review-count">
                  {data.summary.pending_reviews.toString().padStart(2, "0")}
                </div>
              </section>
              <section className="panel status-panel">
                <h2>Resource Health</h2>
                <div className="status-line">
                  <span>Groq analysis</span>
                  <strong>
                    {data.system.ai_status === "success"
                      ? "Available"
                      : data.system.ai_status.replaceAll("_", " ")}
                  </strong>
                </div>
                <div className="status-line">
                  <span>Scheduled checks</span>
                  <strong>
                    {data.system.scheduler_enabled ? "Enabled" : "Off"}
                  </strong>
                </div>
                <div className="status-line">
                  <span>Not yet checked / errors</span>
                  <strong>
                    {data.summary.unverified} / {data.summary.errors}
                  </strong>
                </div>
                <Link to="/system" className="text-link">
                  View system details ↗
                </Link>
              </section>
            </div>
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <h2>Recent Verification Activity</h2>
                  <p>Latest checks across your resource directory.</p>
                </div>
                <Link to="/history" className="text-link">
                  View all history →
                </Link>
              </div>
              {data.results.length ? (
                <ResultsTable results={data.results} lenders={data.lenders} />
              ) : (
                <EmptyState title="Your first check starts here">
                  Choose Verify All to create a verification history.
                </EmptyState>
              )}
            </section>
            <div className="page-footnote">
              Status cards reflect each lender’s latest result. Last check:{" "}
              <Timestamp value={data.summary.last_verification_time} />
            </div>
          </>
        )
      )}
    </>
  );
}
