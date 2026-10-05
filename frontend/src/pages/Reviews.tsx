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
  Pagination,
  Score,
  Timestamp,
} from "../components/ui";
import ReviewDialog, { type ReviewSelection } from "../components/ReviewDialog";

export default function Reviews() {
  const { mutationsDisabled } = useWorkspace();
  const [offset, setOffset] = useState(0);
  const resource = useResource(() => api.pending(offset), String(offset));
  const [review, setReview] = useState<ReviewSelection | null>(null);
  return (
    <>
      <PageHeader
        eyebrow="HUMAN OVERSIGHT"
        title="Review queue"
        description="Investigate possible concerns and record a decision. No automatic data edits."
      />
      <div className="notice">
        Approval accepts a finding for review purposes. It does not change the
        verification status or certify the lender.
      </div>
      {resource.loading ? (
        <LoadingState />
      ) : resource.error ? (
        <ErrorState message={resource.error} retry={resource.reload} />
      ) : (
        resource.data && (
          <>
            {resource.data.length ? (
              <div className="review-list">
                {resource.data.map((result) => (
                  <article key={result.id} className="panel review-card">
                    <div className="panel-title">
                      <div>
                        <Link
                          to={`/lenders/${result.lender_id}?result=${result.id}`}
                          className="review-name"
                        >
                          {result.lender_name}
                        </Link>
                        <p className="caption">
                          Result #{result.id} ·{" "}
                          <Timestamp value={result.checked_at} />
                        </p>
                      </div>
                      <div className="actions">
                        <Badge value={result.status} />
                        <Score value={result.confidence_score} />
                      </div>
                    </div>
                    <h3>Why this was flagged</h3>
                    <ul className="findings">
                      {result.detected_changes.map((change, index) => (
                        <li key={index}>{change.message}</li>
                      ))}
                    </ul>
                    <div className="review-ai">
                      <span className="eyebrow">AI-ASSISTED ANALYSIS</span>
                      <p>
                        {result.ai_analysis?.reason ||
                          (result.ai_status === "disabled"
                            ? "AI analysis is not enabled. Deterministic verification is still active."
                            : "No AI explanation is available for this result.")}
                      </p>
                    </div>
                    {result.ai_analysis?.uncertain_findings.length ? (
                      <p className="muted">
                        Uncertainty:{" "}
                        {result.ai_analysis.uncertain_findings.join("; ")}
                      </p>
                    ) : null}
                    <div className="review-card-footer">
                      <div className="actions">
                        <Link
                          className="text-link"
                          to={`/lenders/${result.lender_id}?result=${result.id}`}
                        >
                          View Details →
                        </Link>
                        <ExternalLink url={result.source_url} />
                      </div>
                      <div className="actions">
                        <button
                          className="button secondary"
                          disabled={mutationsDisabled}
                          onClick={() =>
                            setReview({ result, action: "reject" })
                          }
                        >
                          Reject Finding
                        </button>
                        <button
                          className="button"
                          disabled={mutationsDisabled}
                          onClick={() =>
                            setReview({ result, action: "approve" })
                          }
                        >
                          Approve Finding
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            ) : (
              <section className="panel">
                <EmptyState
                  title={
                    offset ? "No more pending reviews" : "Review queue is clear"
                  }
                >
                  Everything currently requiring human review has been resolved.
                </EmptyState>
              </section>
            )}
            <Pagination
              offset={offset}
              count={resource.data.length}
              onChange={setOffset}
            />
          </>
        )
      )}
      {review && (
        <ReviewDialog
          selection={review}
          onClose={() => setReview(null)}
          onDone={() => {
            setReview(null);
            if (offset) setOffset(0);
            resource.reload();
          }}
        />
      )}
    </>
  );
}
