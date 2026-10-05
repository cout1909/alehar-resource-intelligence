# Phase 2 validation

Validated on 2026-10-04 (Asia/Calcutta), using Python 3.12.10, Node 20.17.0,
and Microsoft Edge on Windows. This extends the existing Phase 1 application.

## Baseline and final checks

| Check | Result |
| --- | --- |
| Phase 1 baseline, before any changes | 71 passed; one dependency warning |
| Final backend pytest suite | 96 passed, including all 71 original tests |
| Ruff configured lint checks | Passed |
| Ruff formatting | Passed |
| pip dependency compatibility | No broken requirements found |
| React/TypeScript production build | Passed, Vite 6.4.3 |
| Playwright browser workflow tests | 2 passed |
| Frontend dependency install audit | 0 vulnerabilities reported |
| Six-page live browser smoke | Passed; no browser JavaScript errors |
| Desktop visual inspection | Completed from browser screenshot |
| Mobile overflow / offline error handling | Passed browser tests |

The original tests were preserved, with formatting/import cleanup only. API
version 0.1.0 remains for compatibility. The Phase 2 frontend is version 0.2.0.
Exact backend versions are in requirements-lock.txt; frontend versions are in
frontend/package-lock.json. Test tooling is separate from normal runtime usage.

## Backend coverage added

- Disabled AI, missing key/model, unsupported provider, and lazy initialization.
- Mocked structured extraction and analysis; unsupported evidence rejected.
- Groq timeout, authentication, rate-limit, provider, initialization, and
  malformed-output failures preserve deterministic outcomes.
- AI can add review concerns but cannot clear a deterministic mismatch or
  change confidence/lender business fields.
- Approve/reject, notes, timestamps, pending queue, invalid input, and conflict
  on repeated review decisions. Lender and verification facts remain unchanged.
- Summary uses latest results per lender; review counts cover historical results.
- History filtering, system status, secret exclusion, and exact-origin CORS.
- Additive migration backup, historical preservation, and idempotency.
- Scheduler disabled mode, lifecycle, overlap prevention, and continuing after
  a lender failure.

Tests prohibit real HTTP/DNS and use temporary databases and mocked Groq.
No automated test requires the real provider key.

## Browser workflows

Tests start an isolated FastAPI server on port 8001 and a frontend on 5174.
That server uses a temporary database, synthetic source responses, and disabled
AI. It is never imported into the normal application and does not alter alehar.db.

The tests exercise:

1. Dashboard loading, Verify All, lender search, lender detail, Verify Now,
   deterministic evidence, and AI-disabled messaging.
2. Pending queue, canceling a decision, approving with a note, rejecting a
   finding, cleared queue, filtered history, and saved review-note display.
3. System status, absence of a key field in the UI, mobile viewport layout,
   backend-offline messaging, and a Retry control.

The first sandboxed run passed both browser tests but left its test server
processes running during Windows cleanup. The processes were stopped and the
complete suite was rerun with appropriate process permissions: **2 passed,
exit code 0**, including clean test-server shutdown.

## Existing database preservation

Before migration the real database had 8 lenders and 3 verification results.
The additive migration preserved all of them and created:

`.backups/alehar.pre-phase2.20261004T052227424436Z.db`

No production/demo lender fields were edited. Old non-verified results were
marked pending; old verified results were marked not required. Later checks
append results normally. Historical pending findings remain pending until a
human decides them; a newer successful check does not silently close them.

## Live API, source, and Groq validation

The normal backend and frontend were started on ports 8000 and 5173. Health,
Swagger, summary, lenders, detail, reviews, history, and system status respond.
All six React pages loaded against the real backend without browser errors.

- The initial model identifier returned Groq HTTP 404. The app saved the
  deterministic result and a sanitized AI-unavailable outcome.
- Groq's authenticated model listing showed `openai/gpt-oss-20b` as available.
  The backend was configured to use that model through Groq.
- A structured extraction diagnostic succeeded.
- A real UGRO Capital verification saved **both structured extraction and AI
  analysis**, with AI status `success` (result #5). Its confidence stayed under
  deterministic control.
- A real sequential batch checked **all 8 lender sources**: **7 verified,
  1 review required, 0 source unavailable, 0 errors**.
- The batch's AI operations encountered output-validation failures and Groq
  HTTP 429 rate limits. Every deterministic outcome was still saved. This is
  live fallback evidence, not a claim that all eight AI analyses succeeded.
- The system reports the most recent AI outcome for the currently configured
  model, so it may show unavailable after a quota/validation failure even though
  an earlier AI-assisted check succeeded. A later verification retries AI.
- After loading the final code, another live UGRO Capital check succeeded
  (result #14): extraction and analysis saved, confidence 100, AI status success.
  The final system check reported backend online, database connected, AI success,
  and scheduler disabled. Swagger returned HTTP 200, and the six-page browser
  smoke check passed again against the running final application.

Approve/reject UI actions were tested only in the isolated database. Real
pending findings were left for the user to review.

## Credential handling and remaining limits

The supplied key is stored only in the ignored backend .env. A scan of 94
source, build, documentation, and log files plus six API responses found **zero
copies of that key outside the intended .env file**. The frontend receives no
key; raw provider error bodies and prompts are not exposed. Application AI
enrichment explicitly disables ambient LangSmith tracing.

Live Groq remains subject to account quotas and model availability. A shared
credential should be rotated in the provider account and replaced locally.
Scheduler behavior was verified through lifecycle/job tests, not by waiting
168 hours. Authentication and production hardening remain outside Phase 2.
Matching identity and confidence 100 do not validate financial facts.
