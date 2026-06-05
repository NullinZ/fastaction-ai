# Contributing to FastAction

Thanks for your interest in FastAction. The project is currently early-stage, so contributions should keep the public API small, explicit, and easy to review.

## Project Boundary

FastAction is a reusable engine. It should not contain host-specific business logic, real customer data, real tokens, private URLs, or organization-specific API registrations.

Reusable FastAction code belongs in this repository:

- schemas and protocols
- registries
- planners
- provider integrations
- policy and confirmation mechanisms
- persistence models
- generic workbench UI
- tests and documentation

Host applications should keep these outside FastAction:

- business API registration data
- tenant-specific context
- real user sessions and tokens
- business adapters
- real API execution
- customer records and attachments

## Development Setup

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev,server]"
```

For the workbench:

```bash
cd frontend/workbench
npm ci
npm run build
```

## Required Checks

Run these before opening a pull request:

```bash
python scripts/validate_fastaction_boundaries.py
python -m ruff check src tests scripts
PYTHONPATH=src python -m pytest tests/fastaction -q
python -m pip wheel . --no-deps -w dist
cd frontend/workbench && npm run build
```

## Coding Guidelines

- Keep APIs typed and explicit.
- Prefer small, composable modules over framework-heavy abstractions.
- Store references to secrets using `secret_ref`; do not store real secrets.
- Treat write operations and external side effects as confirmable by default.
- Add focused tests for behavior, security boundaries, and migration risks.
- Keep docs synchronized when changing protocol, schemas, or behavior.

## Commit Style

Use concise conventional-style prefixes where possible:

```text
feat: add provider registry endpoint
fix: reject blocked API with actionable reason
docs: clarify host execution boundary
test: cover context policy hook
ci: add workbench build
```

## Pull Requests

Pull requests should include:

- what changed
- why it changed
- how it was verified
- any public API or migration impact
- any security or host-boundary impact

Do not include secrets, private endpoints, customer examples, or organization-specific data in issues, tests, screenshots, or fixtures.
