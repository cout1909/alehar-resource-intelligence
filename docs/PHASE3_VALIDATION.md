# Phase 3 validation

Validated 5 October 2026. Public GitHub, Render Free backend and Vercel frontend are deployed. Production API, anonymous incognito browsing, mobile layout and restart recovery passed. Video recording remains pending; local Docker Desktop remains unavailable.

## Baseline and final checks

| Check | Result |
| --- | --- |
| Original backend baseline | 96 passed |
| Original frontend baseline | Production build passed |
| Original browser baseline | 2 passed |
| Final backend | 123 passed |
| Final frontend | Production build passed |
| Local browser workflows | 2 passed: verification/review/history and mobile/offline recovery |
| Public-demo browser workflow | 1 passed: read access, disabled controls, direct POST rejection, unchanged results, scheduler off, one shared status request |
| Real-data browser check | Eight curated records with provenance; actual pages captured; no page errors or mutations during browsing; mobile fits viewport |
| Static Python check | Ruff passed |
| Publication scan | No matching credentials in eligible files or browser assets; required ignore rules present |
| Docker | Render cloud image build and startup passed; local Docker Desktop unavailable |
| GitHub CI | Backend/build/browser workflow passed remotely |
| Production API | Health, eight saved results, exact CORS, hidden docs, and all four mutation guards passed |
| Incognito browser | Fresh Edge context without inherited cookies/login: routes, provenance, flagged explanation, disabled controls and mobile layout passed |
| Render restart | All eight saved results identical before and after restart |

## Final real-source run

The [machine-readable report](verification-report.json) records actual result IDs, UTC check times, signals, model and fallback messages. The final run used 10-second pauses and a 6,000-character AI input bound. No totals were targeted or fabricated.

| Measure | Actual count |
| --- | --- |
| Curated records monitored | 8 |
| Verified | 7 |
| Review required | 1 |
| Source unavailable | 0 |
| Errors | 0 |
| AI success | 2 |
| AI fallback | 6 |

Groq model: `openai/gpt-oss-20b`. ICICI Bank and SIDBI had successful AI analysis in the final run. Six AI outputs failed structure/source-evidence validation and retained deterministic results. Earlier runs also encountered rate limits. This is evidence of working fallback, **not** evidence that all AI analyses succeeded. AI reliability remains a material demo limitation.

Northern Arc Capital is the final review-required record. Its source title uses Northern Arc; the full stored name was absent from bounded extraction. Domain matched. The system conservatively asks for confirmation rather than asserting the directory is wrong. Name-matching thresholds were not relaxed to make the record pass.

## Quality changes justified by observed evidence

- Clarified missing-name findings to distinguish an unconfirmed full identity from a proven wrong record.
- Made omitted descriptions explicit to the AI and rejected positive description comparisons when no description was imported. A prior live output claimed "Description matches" despite an omitted description; a regression test covers that failure.
- Kept exact quotation validation and deterministic fallback. Did not weaken the evidence guard to improve AI success totals.
- Labeled heuristic scores and separated deterministic and AI panels; source provenance and flagged explanations are directly visible.
- Historical results are retained, including earlier uncertain/incorrect AI interpretations. They are not certified facts. Older pending findings are not silently approved or removed, and pending-review counts can exceed latest-record review counts.

## Safety and data preservation

New backend tests cover all four mutation endpoints in public mode, readable routes, scheduler/service guards, disabled docs, allowed/disallowed CORS, malformed origin rejection, sanitized unexpected errors, dataset bounds, idempotent import, non-demo preservation and retained review history. Existing SSRF, source-failure, provider-fallback and review tests still pass.

The curated demo runs from `alehar-demo.db`; the original Phase 2 `alehar.db` remains intact. Consistent SQLite backups were created before imports into the populated demo DB. Migration changes add nullable provenance columns. No credentials were printed or added to code. `.env` stays local and ignored. No Git repository/history existed at validation time; no claim of committed-history scanning is made.

The frontend shares concurrent reads and does not initiate verification while browsing. Requests have timeouts. Batch verification remains sequential, and manual/scheduled work uses the existing single-process lock. Health requests do not call Groq or fetch sources.

## Outstanding external work

Cloud deployment and container validation are complete. Local Docker Desktop validation remains blocked by the unavailable local engine. Video recording/upload is pending; draft scripts and production screenshots are ready. No outreach was sent.

## Free-hosting preparation

Render Free + Vercel + public GitHub were authorized after the original local phase. Three additional backend tests verify idempotent snapshot restoration, recovery after SQLite loss, required read-only mode, and preservation of existing local data. Public browser tests now use the actual bundled snapshot. No live source or Groq request occurs at startup.
