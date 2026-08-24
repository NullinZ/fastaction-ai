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
    database_pool_size: int = _env_int("FASTACTION_DATABASE_POOL_SIZE", 5)
    database_max_overflow: int = _env_int("FASTACTION_DATABASE_MAX_OVERFLOW", 5)
    database_pool_timeout_seconds: int = _env_int("FASTACTION_DATABASE_POOL_TIMEOUT_SECONDS", 5)
    database_pool_recycle_seconds: int = _env_int("FASTACTION_DATABASE_POOL_RECYCLE_SECONDS", 1800)
    database_idle_transaction_timeout_ms: int = _env_int(
        "FASTACTION_DATABASE_IDLE_TRANSACTION_TIMEOUT_MS", 60000
    )
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
