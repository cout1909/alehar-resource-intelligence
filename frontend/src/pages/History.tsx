import { useState } from "react";
import { api } from "../api/client";
import { useResource } from "../hooks/useResource";
import ResultsTable from "../components/ResultsTable";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PageHeader,
  Pagination,
} from "../components/ui";

export default function History() {
  const [lender, setLender] = useState("");
  const [status, setStatus] = useState("");
  const [review, setReview] = useState("");
  const [offset, setOffset] = useState(0);
  const query = new URLSearchParams({ limit: "50", offset: String(offset) });
  if (lender) query.set("lender_id", lender);
  if (status) query.set("status", status);
  if (review) query.set("review_status", review);
  const lenders = useResource(api.lenders);
  const resource = useResource(
    () => api.history(`?${query}`),
    query.toString(),
  );
  return (
    <>
      <PageHeader
        eyebrow="VERIFICATION HISTORY"
        title="Verification history"
        description="Every source check and its recorded review decision, newest first."
      />
      <div className="filters">
        <label>
          Lender
          <select
            value={lender}
            onChange={(event) => {
              setLender(event.target.value);
              setOffset(0);
            }}
          >
            <option value="">All lenders</option>
            {lenders.data?.lenders.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>
        <label>
          Verification status
          <select
            value={status}
            onChange={(event) => {
              setStatus(event.target.value);
              setOffset(0);
            }}
          >
            <option value="">All statuses</option>
            {["VERIFIED", "REVIEW_REQUIRED", "SOURCE_UNAVAILABLE", "ERROR"].map(
              (value) => (
                <option key={value}>{value}</option>
              ),
            )}
          </select>
        </label>
        <label>
          Review status
          <select
            value={review}
            onChange={(event) => {
              setReview(event.target.value);
              setOffset(0);
            }}
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
      {resource.loading ? (
        <LoadingState />
      ) : resource.error ? (
        <ErrorState message={resource.error} retry={resource.reload} />
      ) : (
        resource.data && (
          <section className="panel">
            {resource.data.length ? (
              <ResultsTable
                results={resource.data}
                lenders={lenders.data?.lenders || []}
              />
            ) : (
              <EmptyState title="No matching verification results">
                Run a verification or adjust your filters.
              </EmptyState>
            )}
            <Pagination
              offset={offset}
              count={resource.data.length}
              onChange={setOffset}
            />
          </section>
        )
      )}
    </>
  );
}
