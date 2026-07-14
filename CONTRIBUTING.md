# Contributing to Verxlite

Thanks for your interest in contributing! This document covers the basics.

## Development setup

1. Fork & clone the repo.
2. Backend: `cd api && poetry install`
3. Frontend: `cd web && npm install --legacy-peer-deps`
4. Worker: `cd worker && poetry install`
5. Start infra: `docker-compose up -d db redis`
6. Init the DB: `cd api && poetry run python ../scripts/init_db.py`
7. Start the API: `cd api && poetry run uvicorn main:app --reload`
8. Start the web: `cd web && npm run dev`

## Code style

- Python: `ruff` + `black` (line-length 100). Run `ruff check .` and `black .` before committing.
- TypeScript: `next lint` (ESLint with `next/core-web-vitals`).
- All new code must have type annotations / TypeScript types.

## Tests

- Backend: `pytest tests/` from the repo root.
- Frontend: (TBD) `npm test`.
- Every PR must keep the test suite green.

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: add post-meeting followup workflow
fix: prevent double-prefixed routes
docs: update README
refactor: extract auth into deps module
test: add encryption round-trip tests
chore: bump dependencies
```

## Pull requests

- Keep PRs small and focused.
- Include tests for new features.
- Update documentation for user-facing changes.
- Make sure CI passes before requesting review.

## Reporting bugs

Open a GitHub Issue with:
- Verxlite version (or git commit)
- Python / Node version
- Steps to reproduce
- Expected vs actual behavior
- Logs / screenshots

## Security reports

**Do NOT open a public issue for security vulnerabilities.**
Email `security@verxlite.dev` instead.
