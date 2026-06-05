# Changelog

All notable changes to FastAction will be documented in this file.

The project follows semantic versioning after the first stable release. Before `1.0.0`, minor versions may include API changes, and migration notes will be listed here.

## Unreleased

### Added

- GitHub Actions CI for Python tests, boundary validation, packaging, and workbench builds.
- CodeQL workflow for Python and JavaScript/TypeScript analysis.
- Dependabot configuration for Python, npm, and GitHub Actions dependencies.
- Issue templates, pull request template, contribution guide, security policy, code of conduct, and release process.

### Changed

- Expanded package metadata for public package indexes.
- Replaced local-machine paths in worklog commands with repository-relative commands.

## 0.1.0 - 2026-06-06

### Added

- Initial FastAction engine package.
- API, provider, identity, card, knowledge, run, execution result, and test-message schemas.
- In-memory registries and optional SQLAlchemy persistence.
- Deterministic planner and LLM planner integration points.
- Provider integrations for OpenAI-compatible APIs, Anthropic, Qwen, Doubao, Mimo, DeepSeek, and Qwen balanced model-pool routing.
- FastAPI interface under `/fastaction`.
- Generic workbench frontend.
- Architecture, workbench, development plan, migration boundary, and worklog documentation.
