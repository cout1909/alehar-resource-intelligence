import type { Lender } from "../types/api";
import { ExternalLink, Timestamp } from "./ui";

export default function Provenance({ lender }: { lender: Lender }) {
  return (
    <section className="panel padded provenance" aria-label="Data Provenance">
      <div className="panel-title">
        <h2>Data Provenance</h2>
        <span className="demo-tag">
          {lender.alehar_url ? "CURATED PUBLIC RECORD" : "ILLUSTRATIVE RECORD"}
        </span>
      </div>
      <dl className="facts horizontal">
        <div>
          <dt>Alehar public source</dt>
          <dd>
            <ExternalLink url={lender.alehar_url}>
              Open Alehar directory ↗
            </ExternalLink>
          </dd>
        </div>
        <div>
          <dt>Trusted verification source</dt>
          <dd>
            <ExternalLink url={lender.verification_source_url}>
              Open Source ↗
            </ExternalLink>
          </dd>
        </div>
        <div>
          <dt>Source type</dt>
          <dd>{lender.source_type.replaceAll("_", " ").toLowerCase()}</dd>
        </div>
        <div>
          <dt>Retrieved for this dataset</dt>
          <dd>
            {lender.retrieved_at ? (
              <Timestamp value={lender.retrieved_at} />
            ) : (
              "Not recorded"
            )}
          </dd>
        </div>
        <div>
          <dt>Last checked</dt>
          <dd>
            <Timestamp value={lender.last_verified_at} />
          </dd>
        </div>
      </dl>
      <p className="caption">
        {lender.source_notes ||
          "Legacy demonstration record. No Alehar provenance has been established for this entry."}
      </p>
    </section>
  );
}
