from fastaction.domain.enums import ProviderKind
from fastaction.providers import ProviderMessage, build_provider, provider_presets


def test_provider_presets_include_required_default_providers():
    providers = {item.provider for item in provider_presets()}

    assert ProviderKind.OPENAI in providers
    assert ProviderKind.ANTHROPIC in providers
    assert ProviderKind.QWEN in providers
    assert ProviderKind.DOUBAO in providers
    assert ProviderKind.MIMO in providers
    assert ProviderKind.DEEPSEEK in providers


def test_openai_compatible_provider_builds_json_schema_payload():
    config = next(item for item in provider_presets() if item.provider == ProviderKind.OPENAI)
    provider = build_provider(config)
    payload = provider.build_payload(
        [ProviderMessage(role="user", content="Plan")],
        json_schema={"name": "planner", "schema": {"type": "object", "properties": {}}},
    )

    assert payload["model"] == config.model
    assert payload["response_format"]["type"] == "json_schema"
    assert payload["messages"][0]["role"] == "user"


def test_mimo_provider_uses_official_openai_compatible_url():
    config = next(item for item in provider_presets() if item.provider == ProviderKind.MIMO)
    provider = build_provider(config)

    assert provider.chat_url() == "https://api.mimo-v2.com/v1/chat/completions"


def test_qwen_balanced_service_provider_builds_model_pool_payload():
    config = next(item for item in provider_presets() if item.id == "qwen-balanced-service")
    provider = build_provider(config)
    payload = provider.build_payload([ProviderMessage(role="user", content="Plan")])

    assert payload["service"] == "qwen_balanced_model_pool"
    assert payload["model"] == "auto"
    assert payload["quota_source"] == "local_estimate"


def test_anthropic_provider_builds_messages_payload():
    config = next(item for item in provider_presets() if item.provider == ProviderKind.ANTHROPIC)
    provider = build_provider(config)
    payload = provider.build_payload(
        [
            ProviderMessage(role="system", content="System"),
            ProviderMessage(role="user", content="Plan"),
        ]
    )

    assert payload["model"] == config.model
    assert payload["system"] == "System"
    assert payload["messages"] == [{"role": "user", "content": "Plan"}]
