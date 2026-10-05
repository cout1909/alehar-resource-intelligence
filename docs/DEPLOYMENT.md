# Approved free deployment

Target: public GitHub `cout1909/alehar-resource-intelligence`, Render Free Web Service, Vercel frontend, provider-generated URLs. Budget: zero. No paid disk or managed database is needed or authorized.

## Safe re-creatable state

Render's [free filesystem is ephemeral](https://render.com/docs/free). `PUBLIC_DEMO_SNAPSHOT=true` restores `data/alehar_demo_lenders.json` and `data/public_demo_results.json` into disposable SQLite on startup. The snapshot contains eight real public checks (7 verified, 1 review required), dated evidence, and successful AI or fallback explanations. It contains no review notes, credentials or private data. It is clearly labeled as a saved snapshot in the UI.

Restoration is atomic, idempotent and entirely offline. Original verification timestamps are retained. Unexpected existing data is never overwritten: startup fails with a safe message. Updating the snapshot requires a deliberate reviewed source change; use a new versioned disposable DB filename if retaining an older filesystem. Local `PUBLIC_DEMO_SNAPSHOT=false` preserves normal persistent SQLite and manual verification/review behavior.

## Render setup

Use the root `render.yaml` Blueprint, or create one Docker Web Service from the GitHub repository with these exact settings:

| Setting | Value |
| --- | --- |
| Runtime | Docker, root Dockerfile |
| Plan | Free |
| Health check | /health |
| APP_ENV | production |
| DATABASE_URL | sqlite:////tmp/alehar-public-demo-v1.db |
| PUBLIC_DEMO_MODE | true |
| PUBLIC_DEMO_SNAPSHOT | true |
| ENABLE_DOCS | false |
| SCHEDULER_ENABLED | false |
| AI_ENABLED | false |
| AI_PROVIDER | groq |
| AI_MODEL | openai/gpt-oss-20b |
| ALLOWED_ORIGINS | Exact final HTTPS Vercel origin; no wildcard |

`python -m scripts.serve` starts one worker on the provider's PORT. Docker runs as UID 10001; `/tmp` is writable without a disk. No database or secret is copied into the image. The only committed demo state is the reviewed JSON snapshot. Native alternative: Python 3.12, `pip install -r requirements-lock.txt`, `python -m scripts.serve`.

The backend can start before the frontend URL is known using a deliberately nonmatching placeholder origin such as `https://frontend-not-configured.invalid`, then replace it with the actual Vercel origin before end-to-end acceptance. Do not declare deployment complete until the real exact origin is configured.

## Required Render secret checkpoint

As soon as the backend service exists, stop for the owner to configure their secret: Render Dashboard -> backend service -> **Environment** -> **Add Environment Variable** -> key `GROQ_API_KEY` -> enter the value privately -> **Save, rebuild, and deploy** (or the equivalent save/deploy action shown).

Do not place the value in Git, frontend variables or chat. Saved demo results do not require a runtime key. AI remains disabled in the snapshot deployment; even if enabled later, public mutation and scheduler guards still prevent visitor-triggered calls. Do not temporarily expose write mode to populate data.

## Vercel

Import the public repository. Root directory: `frontend`. Framework: Vite. Install: `npm ci`. Build: `npm run build`. Output: `dist`. Set **Production** `VITE_API_BASE_URL` to the actual HTTPS Render URL, then deploy. SPA routing is prepared in `frontend/vercel.json`.

Set Render `ALLOWED_ORIGINS` to the exact provider-generated Vercel production URL afterward. Rebuild the frontend whenever its API URL changes. Do not copy GROQ_API_KEY or backend environment files into Vercel.

## Accounts and budget

GitHub authentication is available through Windows Credential Manager. Render and Vercel require their normal browser/CLI authorization; never paste account passwords or tokens into chat. Render CLI `login` opens its browser authorization flow. Select only the intended workspace. Use the free service plan and no add-on databases/disks. Do not approve paid upgrades or overage spending. Provider quota exhaustion may pause the demo.

## Verification and cold starts

After each deployment inspect build/runtime logs; fix and redeploy failed revisions. Check `/health`, all frontend routes, eight records and provenance, saved AI/fallback results, history and review queue. Confirm docs are unavailable, scheduler off, and every verification/review POST returns 403 without DB changes. Restart the backend and verify identical saved results are restored.

Open the final frontend in a fresh isolated/incognito browser context with no stored cookies or cache. Confirm CORS and frontend-backend requests work anonymously. Test direct links to `/lenders/3` and `/lenders/6`, and mobile layout. Then update README with confirmed live URLs and capture production screenshots.

Render Free sleeps after inactivity. The UI allows up to 90 seconds for a read and explains the cold-start delay. Before sending the LinkedIn message, open the live demo once and wait for the data to load. This is a one-time pre-send check, not a keep-alive bot. Outreach remains a draft and is not sent automatically.

## Recovery and local Docker

Rollback the code/image and use its matching snapshot; disposable state can be recreated from public JSON. Preserve local development databases and backups. Never replace a local database with the public snapshot without explicitly choosing a separate file.

Docker Desktop was unavailable during initial local validation. `docker build -t alehar-resource-intelligence .` and a public-snapshot run should be checked once available. Render's build/log/health checks must pass before accepting the cloud deployment. No claim of local Docker validation is made.
