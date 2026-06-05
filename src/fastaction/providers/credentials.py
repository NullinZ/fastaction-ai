from __future__ import annotations

import os

from fastaction.schemas import ProviderConfig


def resolve_provider_api_key(config: ProviderConfig) -> str | None:
    if config.credentials.api_key:
        return config.credentials.api_key
    if config.credentials.secret_ref:
        return os.getenv(config.credentials.secret_ref)
    return None


def provider_secret_status(config: ProviderConfig) -> dict[str, str | bool | None]:
    api_key = resolve_provider_api_key(config)
    return {
        "mode": config.credentials.mode,
        "secret_ref": config.credentials.secret_ref,
        "configured": bool(api_key),
    }
