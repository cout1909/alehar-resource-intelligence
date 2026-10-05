import { useWorkspace } from "../hooks/useWorkspace";
import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client";
import { useResource } from "../hooks/useResource";
import {
  Badge,
  EmptyState,
  ErrorState,
  ExternalLink,
  LoadingState,
  PageHeader,
  Score,
  Timestamp,
} from "../components/ui";

export default function Lenders() {
  const { mutationsDisabled } = useWorkspace();
  const resource = useResource(async () => {
    const [lenders, latest] = await Promise.all([api.lenders(), api.latest()]);
    return { lenders: lenders.lenders, latest };
  });
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [review, setReview] = useState("");
  const [busy, setBusy] = useState<number | null>(null);
  const [error, setError] = useState("");
  const verify = async (id: number) => {
    setBusy(id);
    setError("");
    try {
      await api.verify(id);
      resource.reload();
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      setBusy(null);
    }
  };
  const latest = new Map(
    resource.data?.latest.map((result) => [result.lender_id, result]),
  );
  const rows =
    resource.data?.lenders.filter(
      (lender) =>
        lender.name.toLowerCase().includes(search.toLowerCase()) &&
        (!status ||
          (latest.get(lender.id)?.status || "UNVERIFIED") === status) &&
        (!review || latest.get(lender.id)?.review_status === review),
    ) || [];
  return (
    <>
      <PageHeader
        eyebrow="RESOURCE DIRECTORY"
        title="Lenders"
        description="Trusted source links, current verification signals, and review decisions."
      />
      <div className="filters">
        <label className="search">
          Search lenders
          <input
            type="search"
            placeholder="Search by lender name…"
            value={search}
            onChange={(event) => setSearch(event.target.value)}
          />
        </label>
        <label>
          Verification status
          <select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
          >
            <option value="">All statuses</option>
            {[
              "VERIFIED",
              "REVIEW_REQUIRED",
              "SOURCE_UNAVAILABLE",
              "ERROR",
              "UNVERIFIED",
            ].map((value) => (
              <option key={value}>{value}</option>
            ))}
          </select>
        </label>
        <label>
          Review status
          <select
            value={review}
            onChange={(event) => setReview(event.target.value)}
          >
            <option value="">All decisions</option>
            {["PENDING", "APPROVED", "REJECTED", "NOT_REQUIRED"].map(
              (value) => (
                <option key={value}>{value}</option>
              ),
            )}
          </select>
        </label>
      </div>
      {error && <ErrorState message={error} />}
      {resource.loading ? (
        <LoadingState />
      ) : resource.error ? (
        <ErrorState message={resource.error} retry={resource.reload} />
      ) : (
        <section className="panel">
          <div className="panel-heading">
            <h2>
              Lender directory <span className="count-pill">{rows.length}</span>
            </h2>
            <span className="muted">Demonstration dataset</span>
          </div>
          {rows.length ? (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Lender</th>
                    <th>Country / type</th>
                    <th>Source</th>
                    <th>Verification</th>
                    <th>Confidence</th>
                    <th>AI</th>
                    <th>Review</th>
                    <th>Last checked</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((lender) => {
                    const result = latest.get(lender.id);
                    return (
                      <tr key={lender.id}>
                        <td>
                          <Link
                            className="table-name"
                            to={`/lenders/${lender.id}`}
                          >
                            {lender.name}
                          </Link>
                          {lender.is_demo && <small>Demo record</small>}
                        </td>
                        <td>
                          {lender.country}
                          <small className="type-label">
                            {lender.lender_type}
                          </small>
                        </td>
                        <td>
                          <ExternalLink url={lender.verification_source_url} />
                        </td>
                        <td>
                          <Badge value={result?.status || "UNVERIFIED"} />
                        </td>
                        <td>
                          <Score value={result?.confidence_score} />
                        </td>
                        <td>
                          {result ? <Badge value={result.ai_status} /> : "—"}
                        </td>
                        <td>
                          {result ? (
                            <Badge value={result.review_status} />
                          ) : (
                            "—"
                          )}
                        </td>
                        <td>
                          <Timestamp value={lender.last_verified_at} />
                        </td>
                        <td>
                          <div className="actions">
                            <Link
                              to={`/lenders/${lender.id}`}
                              className="text-link"
                            >
                              View
                            </Link>
                            <button
                              className="button small secondary"
                              disabled={busy !== null || mutationsDisabled}
                              onClick={() => verify(lender.id)}
                            >
                              {busy === lender.id ? "Checking…" : "Verify"}
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <EmptyState title="No matching lenders">
              Try another search or clear your filters.
            </EmptyState>
          )}
        </section>
      )}
    </>
  );
}
