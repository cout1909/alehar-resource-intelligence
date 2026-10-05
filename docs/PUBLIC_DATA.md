# Public demo dataset

Eight records were selected from the visible [Alehar India lenders directory](https://www.alehar.com/resources/tools/lenders/IND) on 5 October 2026. The directory's public page and embedded public website links were inspected. Each linked official website was checked separately; website access can vary by network, source policy and time.

| Directory record | Official verification source |
| --- | --- |
| HDFC Bank | https://www.hdfc.bank.in/ |
| ICICI Bank | https://www.icici.bank.in/ |
| SIDBI | https://www.sidbi.in |
| Trifecta Capital | https://trifectacapital.in |
| InnoVen Capital | https://www.innovencapital.com/ |
| Northern Arc Capital | https://www.northernarc.com/ |
| Piramal Finance | https://www.piramalfinance.com |
| Red Fort Capital | https://www.redfortcapital.com |

The [source dataset](../data/alehar_demo_lenders.json) is the auditable record of imported fields and retrieval times. The common Alehar URL is intentional: these are entries on one country directory, not invented individual profile URLs. `alehar_url` is the existing field for Alehar provenance.

Descriptions, loan amounts, rates, products, regulatory status and financial metrics are not imported. `Bank` / `Non-Bank` is explicitly attributed to the directory's broad grouping. India indicates directory placement and is not a claim of incorporation or exhaustive geographic coverage.

Northern Arc Capital's full stored name was not found in the current bounded extraction; the official page uses Northern Arc. This is a naming ambiguity to investigate, not an assertion that the company or directory is fraudulent or incorrect. Do not remove "Capital" from matching rules just to improve a dashboard total.

The source pages retain their own terms and ownership. Only a small factual dataset and bounded verification evidence are used. No private Alehar information or personal contacts are included. Research HTML is retained only in ignored local runtime files and is not packaged or published.

## Reproduction

```powershell
python -m scripts.seed_alehar_demo
python -m scripts.verify_demo
```

Both commands use `DATABASE_URL`. Import is idempotent and preserves existing records/results. Verification appends new results and may call Groq; run it only in a trusted local/operator environment. `PUBLIC_DEMO_MODE=true` blocks verification. Final report numbers describe one dated run, not future guarantees. Previous runs remain in history, so pending-review totals may exceed the number of records currently requiring review.
