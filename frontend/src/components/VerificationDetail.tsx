import type { Verification } from "../types/api";
import { Badge, ExternalLink, Score, Timestamp } from "./ui";

export default function VerificationDetail({
  result,
}: {
  result: Verification;
}) {
  const analysis = result.ai_analysis;
  const extracted = result.ai_extracted_data;
  const text = (key: string) =>
    typeof result.evidence[key] === "string"
      ? String(result.evidence[key])
      : "Not available";
  return (
    <>
      <div className="result-heading">
        <div>
          <div className="eyebrow">VERIFICATION RESULT #{result.id}</div>
          <div className="actions">
            <Badge value={result.status} />
            <Badge value={result.review_status} />
          </div>
        </div>
        <Timestamp value={result.checked_at} />
      </div>
      <div className="detail-grid">
        <section className="panel padded">
          <div className="panel-title">
            <h2>Deterministic verification</h2>
            <Score value={result.confidence_score} />
          </div>
          <p className="muted">
            This is a rule-based verification score, not a statistically
            calibrated probability.
          </p>
          <dl className="facts">
            <div>
              <dt>Source reachable</dt>
              <dd>
                {result.source_reachable ? "Yes" : "No"}
                {result.source_http_status &&
                  ` · HTTP ${result.source_http_status}`}
              </dd>
            </div>
            <div>
              <dt>Company name found</dt>
              <dd>
                {result.evidence.name_found === true
                  ? "Yes"
                  : result.evidence.name_found === false
                    ? "Not found"
                    : "Not evaluated"}
              </dd>
            </div>
            <div>
              <dt>Domain consistent</dt>
              <dd>
                {result.evidence.domain_matches === true
                  ? "Yes"
                  : result.evidence.domain_matches === false
                    ? "Review recommended"
                    : "Not evaluated"}
              </dd>
            </div>
          </dl>
          <ul className="findings">
            {result.detected_changes.map((change, index) => (
              <li key={index}>{change.message}</li>
            ))}
          </ul>
          {result.error_message && (
            <p className="notice">{result.error_message}</p>
          )}
        </section>
        <section className="panel padded">
          <div className="panel-title">
            <h2>AI-assisted analysis</h2>
            <Badge value={result.ai_status} />
          </div>
          <p className="muted">
            AI assists with semantic interpretation. Deterministic source checks
            and human review remain authoritative.
          </p>
          {analysis ? (
            <>
              <p className="analysis-reason">
                {analysis.reason || "No additional explanation supplied."}
              </p>
              <h3>Supported findings</h3>
              {analysis.supported_findings.length ? (
                <ul className="findings">
                  {analysis.supported_findings.map((finding, index) => (
                    <li key={index}>{finding}</li>
                  ))}
                </ul>
              ) : (
                <p className="muted">No additional findings.</p>
              )}
              {analysis.uncertain_findings.length > 0 && (
                <>
                  <h3>Uncertainty to review</h3>
                  <ul className="findings">
                    {analysis.uncertain_findings.map((finding, index) => (
                      <li key={index}>{finding}</li>
                    ))}
                  </ul>
                </>
              )}
              <p className="caption">
                Groq · {result.ai_model} · AI findings may be inaccurate.
              </p>
            </>
          ) : (
            <div className="ai-fallback">
              <span className="empty-symbol">◇</span>
              <h3>
                {result.ai_status === "disabled"
                  ? "AI analysis is not enabled."
                  : result.ai_status === "skipped"
                    ? "AI analysis was skipped for this source."
                    : "AI analysis is unavailable."}
              </h3>
              <p>Deterministic verification is still active.</p>
              {result.ai_error && <p className="caption">{result.ai_error}</p>}
            </div>
          )}
        </section>
      </div>
      {result.status !== "VERIFIED" && (
        <section className="panel padded flagged">
          <div className="panel-title">
            <h2>Why this was flagged</h2>
            <Score value={result.confidence_score} />
          </div>
          <ul className="findings">
            {result.detected_changes
              .filter((change) => change.type !== "NO_CHANGE")
              .map((change, index) => (
                <li key={index}>{change.message}</li>
              ))}
          </ul>
          <p>
            {analysis?.reason ||
              "The available source checks do not provide enough evidence to confirm identity. Review the source before accepting this finding."}
          </p>
          <p>
            <strong>Uncertain fields: </strong>
            {[
              ...(analysis?.uncertain_findings || []),
              ...(extracted?.uncertain_fields || []),
            ].join("; ") ||
              "Identity consistency could not be fully established; financial information is outside this check."}
          </p>
          <p>
            <strong>Evidence summary: </strong>
            {result.source_reachable
              ? text("title")
              : "Source could not be retrieved during this check."}
          </p>
          <ExternalLink url={result.source_url}>
            Inspect supporting source ↗
          </ExternalLink>
        </section>
      )}
      <section className="panel padded">
        <div className="panel-title">
          <h2>Source evidence</h2>
          <ExternalLink url={result.source_url} />
        </div>
        <dl className="facts horizontal">
          <div>
            <dt>Page title</dt>
            <dd>{text("title")}</dd>
          </div>
          <div>
            <dt>Fetched domain</dt>
            <dd>{text("fetched_domain")}</dd>
          </div>
          <div>
            <dt>Expected domain</dt>
            <dd>{text("expected_domain")}</dd>
          </div>
        </dl>
        <blockquote>{text("text_excerpt")}</blockquote>
        <p className="caption">
          A bounded excerpt of the fetched public page. No financial facts are
          certified.
        </p>
        {extracted && (
          <details>
            <summary>View AI structured extraction</summary>
            <dl className="facts">
              <div>
                <dt>Company</dt>
                <dd>{extracted.company_name || "Not stated"}</dd>
              </div>
              <div>
                <dt>Description</dt>
                <dd>{extracted.company_description || "Not stated"}</dd>
              </div>
              <div>
                <dt>Entity type</dt>
                <dd>{extracted.entity_type || "Not stated"}</dd>
              </div>
              <div>
                <dt>Products / services</dt>
                <dd>
                  {extracted.products_or_services.join("; ") || "Not stated"}
                </dd>
              </div>
              <div>
                <dt>Geographies</dt>
                <dd>{extracted.geographies.join(", ") || "Not stated"}</dd>
              </div>
              <div>
                <dt>Uncertain fields</dt>
                <dd>
                  {extracted.uncertain_fields.join(", ") || "None reported"}
                </dd>
              </div>
            </dl>
            <p>{extracted.source_summary}</p>
            {extracted.identity_evidence.map((quote, index) => (
              <blockquote key={index}>{quote}</blockquote>
            ))}
          </details>
        )}
      </section>
      {result.reviewed_at && (
        <section className="panel padded">
          <div className="panel-title">
            <h2>Recorded review decision</h2>
            <Badge value={result.review_status} />
          </div>
          <p>{result.review_note || "No note supplied."}</p>
          <p className="caption">
            <Timestamp value={result.reviewed_at} /> · Decision recorded; lender
            data unchanged.
          </p>
        </section>
      )}
    </>
  );
}
