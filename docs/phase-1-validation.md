# Phase 1 completion evidence

Validated locally on 2026-10-04 (Asia/Calcutta), using Python 3.12.10 on Windows.

## Installation and automated checks

- Installed Python 3.12 for the current Windows user, without the system-wide
  launcher, after the default installer stalled awaiting elevation.
- Recreated the existing unusable Python 3.10 virtual environment as `.venv`.
- Installed all dependencies from `requirements.txt` and recorded exact versions
  in `requirements-lock.txt`.
- `python -m pip check`: **No broken requirements found.**
- `.venv\Scripts\python.exe -m pytest -q`: **71 passed**, one third-party
  Starlette deprecation warning about its httpx TestClient adapter.
- All tests are offline with HTTP and DNS mocks; test databases are temporary.

## Running API checks

Started `.venv\Scripts\python.exe -m uvicorn app.main:app --reload` on
`http://127.0.0.1:8000`.

| Check | Observed result |
| --- | --- |
| `GET /health` | HTTP 200, status `ok` |
| `GET /lenders` | HTTP 200, 8 explicitly marked demo entries |
| `GET /lenders/1` | HTTP 200, HDFC Bank demo entry |
| `GET /docs` | HTTP 200, Swagger UI markup present |
| `GET /redoc` | HTTP 200 |
| `POST /lenders/4/verify` with sandbox-blocked network | HTTP 200, recorded `SOURCE_UNAVAILABLE`, confidence 0 |
| `POST /lenders/4/verify` with approved network access | UGRO Capital source HTTP 200; recorded `VERIFIED`, confidence 100 |
| `POST /lenders/1/verify` with approved network access | HDFC Bank source HTTP 200; recorded `VERIFIED`, confidence 100 |
| `GET /verification-results` | 3 saved outcomes, newest first |
| Health after verification | Still `ok` |

Swagger and ReDoc were checked programmatically over HTTP, not through an
interactive browser. No external website availability is guaranteed for future
runs. The unavailable-source live check reflects the execution sandbox's blocked
network, not an outage of the lender's website. Independent offline tests also
cover HTTP failures, timeouts, TLS errors, and connection failures.

The local `alehar.db` contains the demo entries and the three smoke-test results.
Automated tests confirm persisted history after application restart, sequential
batch processing, all four verification outcomes, and unchanged lender business
fields. There are no paid service keys, automatic edits, or background crawlers.

`VERIFIED` and confidence 100 refer only to this MVP's basic source identity
heuristic. They do not validate financial facts or represent statistical certainty.
