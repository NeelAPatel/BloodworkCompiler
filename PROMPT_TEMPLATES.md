# Prompt Templates

Copy one template per Cursor chat. Keep chats small in scope (one task each).

## 1) Implement a parsing helper (pure function + tests)
Task: Extract numeric values and units from strings.
Constraints:
- Handle: "12.3 g/dL", "5,600 IU/L", "< 0.10 mg/L", "NEGATIVE", "trace".
- Return (value_numeric, unit) or (None, unit).
- Add tests in `backend/tests/test_normalize.py`.
- No new dependencies.

## 2) Add a typed API route w/ OpenAPI
Task: Implement `GET /labs?email=<str>&test_name=<str>&from=<date?>&to=<date?>`.
Return: `{ series: [{ x: ISODate, y: float|null, unit: str|null }] }`
Constraints:
- Pydantic response models, async SQLAlchemy query
- Unit tests and one integration test

## 3) Create Alembic migration for index
Task: Add `(user_id, test_name, collected_at)` index on `labs`.
Constraints:
- Reversible migration (downgrade)
- Update tests to assert plan contains the index

## 4) Plotly chart page (Next.js)
Task: `/chart` page with controls for email, test name, date range.
Constraints:
- Fetch JSON from `/labs`, render line+markers, enable hover/zoom
- Minimal styling, no new UI libraries

## 5) Refactor plan-first
Task: Propose a 5-bullet plan to split `run_local.parse_pdf` into helpers, then implement in small diffs with tests.

## 6) Test-first bug fix
Task: Given failing test (paste), propose minimal change to pass; show diff and reasoning.

## 7) RLS policy addition (SQL)
Task: Enable Postgres Row-Level Security on `labs` and `documents`.
Constraints:
- Add policies keyed on session var `app.user_id`
- Provide a FastAPI dependency to set `app.user_id`
- Add tests proving cross-user access is denied

## 8) Presigned S3 upload flow (backend)
Task: Add `/presign` returning PUT URL + fields; adjust `/upload` to register metadata only.
Constraints:
- No PHI in object keys; server never stores plaintext
- Unit tests for signature and content-type enforcement

## 9) OpenTelemetry instrumentation
Task: Add request/route traces and DB spans (no PHI).
Constraints:
- Sampling config; redact attributes
- Tests/mocks to avoid network calls during CI

## 10) Prompt evaluation harness (placeholder)
Task: Create `evals/promptfoo.yaml` with 10 canned questions and expected patterns.
Constraints:
- Script to run evals in CI (skip if secrets missing); produce a simple report artifact
