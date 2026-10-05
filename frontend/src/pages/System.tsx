import { api } from "../api/client";
import { useResource } from "../hooks/useResource";
import {
  ErrorState,
  LoadingState,
  PageHeader,
  Timestamp,
} from "../components/ui";

export default function System() {
  const resource = useResource(api.system);
  const data = resource.data;
  return (
    <>
      <PageHeader
        eyebrow="OPERATIONS"
        title="System status"
        description="Connectivity, optional AI assistance, and scheduled verification."
      >
        <button
          className="button secondary"
          disabled={resource.loading}
          onClick={resource.reload}
        >
          Refresh status
        </button>
      </PageHeader>
      {resource.loading ? (
        <LoadingState />
      ) : resource.error ? (
        <>
          <ErrorState message={resource.error} retry={resource.reload} />
          <section className="panel padded">
            <h2>Backend offline</h2>
            <p>
              Database and AI status cannot be checked until the backend
              reconnects.
            </p>
          </section>
        </>
      ) : (
        data && (
          <>
            <div className="system-grid">
              <section className="panel padded">
                <div className="eyebrow">CORE SERVICES</div>
                <h2>Verification engine</h2>
                <dl className="facts">
                  <div>
                    <dt>Backend</dt>
                    <dd>
                      <span className="service-dot" />
                      Online
                    </dd>
                  </div>
                  <div>
                    <dt>Database</dt>
                    <dd>
                      {data.database_status === "connected"
                        ? "Connected"
                        : "Error"}
                    </dd>
                  </div>
                  <div>
                    <dt>Public demo</dt>
                    <dd>
                      {data.public_demo_mode
                        ? "Read only · actions disabled"
                        : "Off · local actions available"}
                    </dd>
                  </div>
                  <div>
                    <dt>Deterministic checks</dt>
                    <dd>Active</dd>
                  </div>
                  <div>
                    <dt>Current activity</dt>
                    <dd>
                      {data.verification_running
                        ? "Verification in progress"
                        : "Ready"}
                    </dd>
                  </div>
                </dl>
              </section>
              <section className="panel padded">
                <div className="eyebrow">OPTIONAL INTELLIGENCE</div>
                <h2>Groq AI analysis</h2>
                <dl className="facts">
                  <div>
                    <dt>Provider</dt>
                    <dd>{data.ai_provider}</dd>
                  </div>
                  <div>
                    <dt>AI status</dt>
                    <dd>
                      {
                        (
                          {
                            success: "Enabled · last check succeeded",
                            ready: "Enabled · not tested yet",
                            disabled: "Disabled",
                            not_configured: "Not configured",
                            unavailable: "Unavailable · fallback active",
                          } as Record<string, string>
                        )[data.ai_status]
                      }
                    </dd>
                  </div>
                  <div>
                    <dt>Model</dt>
                    <dd>{data.ai_model || "Not configured"}</dd>
                  </div>
                </dl>
                <div className="notice">{data.ai_message}</div>
                <p className="caption">
                  AI can recommend review. It cannot change lender records.
                </p>
              </section>
            </div>
            <section className="panel padded">
              <div className="eyebrow">AUTOMATION</div>
              <h2>Scheduled verification</h2>
              <dl className="facts horizontal">
                <div>
                  <dt>Scheduler</dt>
                  <dd>{data.scheduler_enabled ? "Enabled" : "Disabled"}</dd>
                </div>
                <div>
                  <dt>Interval</dt>
                  <dd>Every {data.verification_interval_hours} hours</dd>
                </div>
                <div>
                  <dt>Next run</dt>
                  <dd>
                    {data.next_scheduled_run ? (
                      <Timestamp value={data.next_scheduled_run} />
                    ) : (
                      "No scheduled run"
                    )}
                  </dd>
                </div>
              </dl>
              <p className="caption">
                Checks run sequentially. Overlapping manual and scheduled checks
                are prevented in this local workspace.
              </p>
            </section>
          </>
        )
      )}
    </>
  );
}
