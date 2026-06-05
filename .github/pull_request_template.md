## Summary

Describe the change and why it is needed.

## Type

- [ ] Bug fix
- [ ] Feature
- [ ] Documentation
- [ ] Refactor
- [ ] Test / CI
- [ ] Security

## Validation

- [ ] `python scripts/validate_fastaction_boundaries.py`
- [ ] `python -m ruff check src tests scripts`
- [ ] `PYTHONPATH=src python -m pytest tests/fastaction -q`
- [ ] `cd frontend/workbench && npm run build`
- [ ] Not applicable, documentation-only change

## Security and Boundary Check

- [ ] No secrets, API keys, tokens, customer data, or host-specific business data were added.
- [ ] Host-specific behavior remains outside the reusable FastAction engine.
- [ ] Write or external-call behavior has confirmation and audit implications documented.

## Compatibility

List any public API changes, migration steps, or backward-compatibility risks.
