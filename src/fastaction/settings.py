from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default
    try:
        return int(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class FastActionSettings:
    db_schema: str = os.getenv("FASTACTION_DB_SCHEMA", "fastaction")
    database_url: str = os.getenv("FASTACTION_DATABASE_URL", "")
    persistence_enabled: bool = _env_bool("FASTACTION_PERSISTENCE_ENABLED", False)
    aliyun_bailian_free_quota_expires_at: str = os.getenv(
        "ALIYUN_BAILIAN_FREE_QUOTA_EXPIRES_AT",
        "",
    )
    qwen_timeout_seconds: int = _env_int("FASTACTION_QWEN_TIMEOUT_SECONDS", 60)


@lru_cache(maxsize=1)
def get_settings() -> FastActionSettings:
    return FastActionSettings()


def reload_settings() -> FastActionSettings:
    get_settings.cache_clear()
    return get_settings()

