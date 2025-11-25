# Change Review

This checklist applies to **every** AI-assisted change and PR.

## Summary (required in PR description)
- [ ] Purpose of change (2–5 bullets)
- [ ] Scope (files/modules touched)
- [ ] Alternatives considered (brief)
- [ ] Risk level (low/med/high) and why

## Tests & Quality
- [ ] Unit tests added/updated for new/changed code
- [ ] `pytest -q` passes locally
- [ ] Type checks pass (mypy/pyright if configured)
- [ ] Lint/format pass (ruff/flake8 + black)

## Security & Privacy
- [ ] No secrets or PHI in code, tests, or logs
- [ ] Logs remain metadata-only (no lab values, names, emails)
- [ ] Error messages are non-sensitive and actionable
- [ ] If encryption/auth/upload logic changed → **security review required**

## Database
- [ ] Schema changes use Alembic migration scripts
- [ ] Migrations are idempotent and reversible (downgrade works)
- [ ] Indexes considered for new query paths
- [ ] Backfill or data migration strategy documented (if needed)

## API & Contracts
- [ ] OpenAPI types accurate; request/response models validated
- [ ] Backward compatibility evaluated (breaking changes called out)
- [ ] Rate limits / input validation where appropriate

## Observability
- [ ] Logs/traces added for key paths (no PHI)
- [ ] Metrics updated (latency, error rate) if endpoints added/changed

## Rollback & Ops
- [ ] Rollback plan documented (how to disable/restore prior behavior)
- [ ] Feature flags or env toggles considered (when risky)
- [ ] CI workflow(s) updated if needed

## Manual sign-off required for
- Encryption, authentication, file uploads, database schema, or any code that can expose PHI.
