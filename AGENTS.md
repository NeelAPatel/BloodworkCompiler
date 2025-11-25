# Agent Config

## Allowed actions
- Create/modify small Python modules (parsers, services, api routes) with tests.
- Write Alembic migrations for schema changes.
- Add/extend Next.js pages for upload & charts.
- Create CI (GitHub Actions) for lint/test/migrate.

## Disallowed actions
- Storing secrets in code or Git history.
- Deploying to cloud or altering production config.
- Modifying encryption unless the task explicitly says so.

## Tools & Conventions
- Python: 3.14+, FastAPI, SQLAlchemy, Alembic, pytest.
- DB: Postgres.
- UI: Next.js (TS), Plotly charts.
- Storage: local FS now, S3 later (presigned).
- Queue: none initially; add Redis/RQ if parsing is slow.

## Review checklist (agent should show)
- [ ] Plan summary of changes (bullets).
- [ ] Diff preview for each file.
- [ ] Tests added/updated and pass locally.
- [ ] No secrets; no PHI in logs.
- [ ] Docs: updated readme or comments if behavior changed.

