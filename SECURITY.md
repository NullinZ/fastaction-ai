# Security Policy

FastAction sits between AI agents and business APIs, so security reports are taken seriously.

## Supported Versions

FastAction is currently pre-1.0. Security fixes are applied to the latest `main` branch until stable release branches exist.

| Version | Supported |
|---|---|
| `main` | Yes |
| `< 0.1.0` | No |

## Reporting A Vulnerability

Please do not open a public issue for a suspected vulnerability.

Report privately through GitHub Security Advisories:

<https://github.com/NullinZ/fastaction-ai/security/advisories/new>

If advisories are unavailable, contact the maintainers through the repository owner profile and include only redacted technical details.

## What To Include

Please include:

- affected version or commit
- minimal reproduction steps
- expected impact
- whether exploitation requires host credentials, admin access, or a configured provider
- suggested fix, if known

Do not include real API keys, access tokens, customer data, private endpoints, or screenshots containing sensitive information.

## Security Design Principles

FastAction is designed around these boundaries:

- Models should only see filtered candidate capabilities.
- Real API execution should happen inside the host application.
- Host applications own final authorization.
- Secrets should be referenced by `secret_ref`, not stored directly.
- Write operations and external side effects should be confirmable and auditable.
- User tokens should not be stored long term by default.

## Disclosure

We aim to acknowledge valid reports within 7 days. Public disclosure should wait until a fix or mitigation is available.
