import { useWorkspace } from "../hooks/useWorkspace";
import { useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api } from "../api/client";
import { useResource } from "../hooks/useResource";
import {
  EmptyState,
  ErrorState,
  ExternalLink,
  LoadingState,
  PageHeader,
  Pagination,
  Timestamp,
} from "../components/ui";
import Provenance from "../components/Provenance";
import { Badge } from "../components/ui";
import VerificationDetail from "../components/VerificationDetail";
import ResultsTable from "../components/ResultsTable";
import ReviewDialog, { type ReviewSelection } from "../components/ReviewDialog";

export default function LenderDetail() {
  const { mutationsDisabled } = useWorkspace();
  const { id = "" } = useParams();
  const [params, setParams] = useSearchParams();
  const selected = params.get("result");
  const [offset, setOffset] = useState(0);
  const resource = useResource(async () => {
    const [lender, history, requested, firstPage] = await Promise.all([
      api.lender(id),
      api.lenderHistory(id, offset),
      selected ? api.result(selected) : Promise.resolve(null),
      offset ? api.lenderHistory(id, 0) : Promise.resolve(null),
    ]);
    if (requested && requested.lender_id !== lender.id)
      throw new Error("This verification belongs to a different lender.");
    return {
      lender,
      history,
      latest: (firstPage || history)[0] || null,
      result: requested || history[0] || null,
    };
  }, `${id}-${selected}-${offset}`);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [review, setReview] = useState<ReviewSelection | null>(null);
  const verify = async () => {
    setBusy(true);
    setError("");
    try {
      const result = await api.verify(Number(id));
      setParams({ result: String(result.id) });
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
      <Link to="/lenders" className="back-link">
        ← Back to lenders
      </Link>
      <PageHeader
        eyebrow="LENDER PROFILE"
        title={data?.lender.name || "Lender detail"}
        description="Stored information, source evidence, and a complete review trail."
      >
        <button
          className="button"
          onClick={verify}
          disabled={
            mutationsDisabled || busy || resource.loading || !!resource.error
          }
        >
          {busy ? "Verifying…" : "↻ Verify Now"}
        </button>
      </PageHeader>
      {error && <ErrorState message={error} />}
      {resource.loading ? (
        <LoadingState />
      ) : resource.error ? (
        <ErrorState message={resource.error} retry={resource.reload} />
      ) : (
        data && (
          <>
            <section className="panel padded">
              <div className="panel-title">
                <h2>Stored data</h2>
                {data.lender.is_demo && (
                  <span className="demo-tag">DEMO RECORD</span>
                )}
              </div>
              <p>
                {data.lender.description ||
                  "Description omitted; this demo makes no claim about financial terms or eligibility."}
              </p>
              <dl className="facts horizontal">
                <div>
                  <dt>Country</dt>
                  <dd>{data.lender.country}</dd>
                </div>
                <div>
                  <dt>Type</dt>
                  <dd>{data.lender.lender_type}</dd>
                </div>
                <div>
                  <dt>Last verified</dt>
                  <dd>
                    <Timestamp value={data.lender.last_verified_at} />
                  </dd>
                </div>
                <div>
                  <dt>Website</dt>
                  <dd>
                    <ExternalLink url={data.lender.website_url}>
                      Visit website ↗
                    </ExternalLink>
                  </dd>
                </div>
                <div>
                  <dt>Verification source</dt>
                  <dd>
                    <ExternalLink url={data.lender.verification_source_url}>
                      Open Official Source ↗
                    </ExternalLink>
                  </dd>
                </div>
              </dl>
            </section>
            <div className="current-status">
              <strong>Current verification status</strong>
              <Badge value={data.latest?.status || "UNVERIFIED"} />
              {selected && data.result?.id !== data.latest?.id && (
                <span>Viewing a historical result below.</span>
              )}
            </div>
            <Provenance lender={data.lender} />
            {data.result ? (
              <>
                <VerificationDetail result={data.result} />
                {data.result.review_status === "PENDING" && (
                  <div className="review-bar">
                    <div>
                      <strong>Human review required</strong>
                      <p>
                        Review the evidence, then record your decision. Lender
                        data will stay unchanged.
                      </p>
                    </div>
                    <div className="actions">
                      <button
                        className="button secondary"
                        disabled={busy || mutationsDisabled}
                        onClick={() =>
                          setReview({ result: data.result!, action: "reject" })
                        }
                      >
                        Reject Finding
                      </button>
                      <button
                        className="button"
                        disabled={busy || mutationsDisabled}
                        onClick={() =>
                          setReview({ result: data.result!, action: "approve" })
                        }
                      >
                        Approve Finding
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : (
              <section className="panel">
                <EmptyState title="No verification yet">
                  Select Verify Now to check this lender’s public source.
                </EmptyState>
              </section>
            )}
            <section className="panel">
              <div className="panel-heading">
                <h2>Verification history</h2>
                <span className="muted">
                  Newest first · Select a result to view its evidence
                </span>
              </div>
              <ResultsTable results={data.history} lenders={[data.lender]} />
              <Pagination
                offset={offset}
                count={data.history.length}
                onChange={setOffset}
              />
            </section>
          </>
        )
      )}
      {review && (
        <ReviewDialog
          selection={review}
          onClose={() => setReview(null)}
          onDone={() => {
            setReview(null);
            resource.reload();
          }}
        />
      )}
    </>
  );
}
