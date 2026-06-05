# Release Process

FastAction is currently pre-1.0. Releases should be small, documented, and easy to roll back.

## Versioning

Before `1.0.0`:

- Patch releases fix defects without intentional protocol changes.
- Minor releases may change public schemas or APIs.
- Breaking changes must be documented in `CHANGELOG.md`.

After `1.0.0`, FastAction should follow semantic versioning:

```text
MAJOR: incompatible public API changes
MINOR: backward-compatible features
PATCH: backward-compatible fixes
```

## Pre-Release Checklist

Run:

```bash
python scripts/validate_fastaction_boundaries.py
python -m ruff check src tests scripts
PYTHONPATH=src python -m pytest tests/fastaction -q
python -m pip wheel . --no-deps -w dist
cd frontend/workbench && npm ci && npm run build
```

Check:

- `CHANGELOG.md` has an entry for the release.
- `pyproject.toml` version is updated.
- README and docs match the shipped behavior.
- No secrets, host-specific registrations, or customer data are present.
- CI is green on `main`.

## Tagging

Use signed tags when possible:

```bash
git tag -s v0.1.0 -m "v0.1.0"
git push origin v0.1.0
```

If signed tags are not available:

```bash
git tag v0.1.0
git push origin v0.1.0
```

## Publishing

The package should be published only from a clean, tagged commit. Avoid publishing from local uncommitted state.

For PyPI publishing, prefer a trusted publishing workflow rather than long-lived API tokens.
