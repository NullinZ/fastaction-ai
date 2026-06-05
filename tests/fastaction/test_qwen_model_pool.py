from datetime import datetime

from fastaction.providers.qwen_model_pool import (
    QWEN_FREE_QUOTA_MODEL_NAMES,
    is_qwen_free_quota_expired,
    parse_qwen_free_quota_expires_at,
)


def test_qwen_model_pool_includes_latest_bailian_free_quota_chat_models():
    models = set(QWEN_FREE_QUOTA_MODEL_NAMES)

    assert "qwen3.7-max" in models
    assert "qwen3.7-max-2026-05-20" in models
    assert "qwen3.7-plus" in models
    assert "qwen3.7-plus-2026-05-26" in models
    assert "deepseek-r1-distill-qwen-1.5b" in models
    assert "deepseek-r1-distill-llama-8b" in models


def test_models_without_current_bailian_free_quota_stay_out_of_pool():
    models = set(QWEN_FREE_QUOTA_MODEL_NAMES)

    assert "mimo-v2.5-pro" not in models
    assert "xiaomi/mimo-v2.5-pro" not in models
    assert "MiniMax/MiniMax-M2.7" not in models
    assert "qwen2.5-14b-instruct-1m" not in models
    assert "qwen2.5-coder-32b-instruct" not in models
    assert "qwen3-4b" not in models


def test_free_quota_expiry_date_filter():
    expires_at = parse_qwen_free_quota_expires_at("2026-06-04")

    assert expires_at is not None
    assert is_qwen_free_quota_expired(
        now=datetime(2026, 6, 5, 0, 0, 0),
        expires_at=expires_at,
    )
    assert not is_qwen_free_quota_expired(
        now=datetime(2026, 6, 4, 12, 0, 0),
        expires_at=expires_at,
    )
