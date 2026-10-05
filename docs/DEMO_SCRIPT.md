# 90-second executive demo

Use the curated local database and saved results. Do not trigger a live batch while recording: public sources and provider quotas vary. Check [the actual verification report](verification-report.json) for the latest run; never promise fixed result totals.

| Time | Screen / action | Suggested narration |
| --- | --- | --- |
| 0–10 sec | Dashboard, independent-proof-of-concept banner | “I noticed a possible recurring verification workflow in Alehar's public resource tools. I built this independent prototype using publicly available information.” |
| 10–25 sec | Five status cards and attention section | “It monitors eight selected public records, compares them with trusted sources, and highlights uncertainty. These are identity checks, not certification of financial information.” |
| 25–40 sec | SIDBI, `/lenders/3`; show provenance and deterministic panel | “Each record links back to Alehar's directory and an official source. Here the identity checks are consistent, and the saved Groq interpretation supports the evidence.” |
| 40–65 sec | Northern Arc Capital, `/lenders/6`; flagged section and source title | “Alehar lists Northern Arc Capital, while this fetched page uses Northern Arc. The full stored name was not found in the bounded text. The system asks a person to resolve that ambiguity; it does not assume the record is wrong. The low heuristic score is not a probability.” |
| 65–80 sec | Review queue; point at Approve Finding / Reject Finding | “The reviewer examines the source and records a decision about the finding. AI never changes business data. Public-demo controls are read only; the local workflow supports decisions.” |
| 80–90 sec | Return to dashboard | “If Alehar finds the approach useful, a future pilot could use approved data and extend this verification workflow based on your feedback.” |

The final Northern Arc result uses deterministic fallback because AI output failed validation. Say this plainly if showing its AI panel. SIDBI demonstrates a successful saved AI result. Use the exact saved routes in [demo-examples.json](demo-examples.json). For an actual decision demonstration, use a disposable copy of the database and a rehearsal finding; do not alter the preserved public demo just to stage the video.
