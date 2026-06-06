import pytest

from fastaction.domain.errors import ProviderError
from fastaction.domain.enums import OperationType, RiskLevel
from fastaction.planner import DeterministicPlanner, LLMPlanner
from fastaction.providers import ProviderResponse
from fastaction.registries import runtime
from fastaction.schemas import APIDefinition, ChatRequest, OptionSetDefinition, ProviderConfig


def make_api(risk=RiskLevel.READ):
    return APIDefinition(
        id="resource.status.get",
        name={"zh": "查询资源状态", "en": "Get resource status"},
        operation_type=OperationType.DETAIL,
        intent={
            "description": "status",
            "examples": {"zh": ["查询资源状态"]},
            "keywords": {"zh": ["状态", "进度"]},
        },
        request={"method": "GET", "endpoint": "/api/v1/resources/{resourceId}/status"},
        parameters={
            "type": "object",
            "required": ["resourceId"],
            "properties": {
                "resourceId": {
                    "type": "string",
                    "label": {"zh": "资源", "en": "Resource"},
                    "description": {"zh": "要查询的资源 ID", "en": "Resource ID to query"},
                    "source": ["context.current_resource.id", "clarify"],
                }
            },
        },
        policy={"risk": risk, "requires_confirmation": risk != RiskLevel.READ},
        render={
            "card_type": "detail_card",
            "field_bindings": {"title": "$.resource.name"},
        },
    )


def test_planner_invokes_api_when_context_resolves_required_param():
    instruction = DeterministicPlanner().plan(
        ChatRequest(
            text="查一下当前状态",
            context={"current_resource": {"id": "res_001"}},
        ),
        [make_api()],
    )

    assert instruction.action == "invoke_api"
    assert instruction.api.id == "resource.status.get"
    assert instruction.params == {"resourceId": "res_001"}


def test_planner_resolves_registered_option_set_aliases_from_text():
    runtime.option_sets.upsert(
        OptionSetDefinition(
            id="example.document_kind",
            name={"zh": "文档类型", "en": "Document kind"},
            options=[
                {"value": "proposal", "label": {"zh": "方案", "en": "Proposal"}, "aliases": ["初稿"]},
                {"value": "contract", "label": {"zh": "合同", "en": "Contract"}},
            ],
        )
    )
    runtime.option_sets.upsert(
        OptionSetDefinition(
            id="example.document_purpose",
            name={"zh": "文档用途", "en": "Document purpose"},
            options=[
                {"value": "review", "label": {"zh": "评审", "en": "Review"}, "aliases": ["内部评审"]},
                {"value": "archive", "label": {"zh": "归档", "en": "Archive"}},
            ],
        )
    )
    api = APIDefinition(
        id="documents.submit",
        name={"zh": "提交文档", "en": "Submit document"},
        operation_type=OperationType.CREATE,
        intent={
            "description": "submit document",
            "examples": {"zh": ["提交文档"]},
            "keywords": {"zh": ["提交文档", "方案"]},
        },
        request={"method": "POST", "endpoint": "/documents"},
        parameters={
            "type": "object",
            "required": ["document_kind", "document_purpose"],
            "properties": {
                "document_kind": {"type": "string", "option_set": "example.document_kind"},
                "document_purpose": {"type": "string", "option_set": "example.document_purpose"},
            },
        },
    )

    instruction = DeterministicPlanner().plan(ChatRequest(text="提交文档：一份初稿，用于内部评审"), [api])

    assert instruction.action == "invoke_api"
    assert instruction.params["document_kind"] == "proposal"
    assert instruction.params["document_purpose"] == "review"


def test_planner_prefers_mentioned_entity_over_current_context():
    api = make_api()
    api.parameters["properties"]["resourceId"]["resolve_entity"] = "resource"
    instruction = DeterministicPlanner().plan(
        ChatRequest(
            text="查询测试资源 0501 的状态",
            context={
                "current_resource": {"id": "res_wrong", "name": "当前默认资源"},
                "available_resources": [
                    {"id": "res_0501", "name": "测试资源 0501"},
                    {"id": "res_0510", "name": "测试资源 0510"},
                ],
            },
        ),
        [api],
    )

    assert instruction.action == "invoke_api"
    assert instruction.params["resourceId"] == "res_0501"


def test_planner_clarifies_when_required_param_missing():
    instruction = DeterministicPlanner().plan(ChatRequest(text="查一下当前状态"), [make_api()])

    assert instruction.action == "clarify"
    assert instruction.api.id == "resource.status.get"
    assert instruction.params == {}
    assert instruction.clarify.missing_params == ["resourceId"]
    assert instruction.clarify.missing_param_details[0].name == "resourceId"
    assert instruction.clarify.missing_param_details[0].label == {"zh": "资源", "en": "Resource"}
    assert instruction.clarify.missing_param_details[0].type == "string"
    assert instruction.clarify.missing_param_details[0].source == ["context.current_resource.id", "clarify"]
    assert instruction.render.card_type == "missing_params_card"
    assert instruction.render.fallback_card_type == "picker_card"
    assert instruction.render.state == "missing_params"
    assert instruction.pending_instruction.api_id == "resource.status.get"


def test_planner_confirms_write_risk():
    instruction = DeterministicPlanner().plan(
        ChatRequest(
            text="查一下当前状态",
            context={"current_resource": {"id": "res_001"}},
        ),
        [make_api(risk=RiskLevel.WRITE)],
    )

    assert instruction.action == "confirm"
    assert instruction.pending_instruction.api_id == "resource.status.get"


@pytest.mark.asyncio
async def test_llm_planner_answers_when_no_api_matches(monkeypatch):
    class FakeProvider:
        async def complete(self, messages, **kwargs):
            assert "No registered API matched" in messages[0].content
            return ProviderResponse(text="我可以先帮您梳理需求。", provider="fake", model="runtime-v2")

    monkeypatch.setattr("fastaction.planner.llm_planner.build_provider", lambda config: FakeProvider())
    instruction = await LLMPlanner().plan(
        ChatRequest(text="随便聊聊", no_api_hit_strategy="llm_answer"),
        [],
        make_provider_config(),
    )

    assert instruction.action == "answer"
    assert instruction.api is None
    assert instruction.provider.id == "fake-answer-provider"
    assert instruction.provider.model == "fake-model"
    assert instruction.provider.runtime_model == "runtime-v2"
    assert instruction.reply["zh"] == "我可以先帮您梳理需求。"


@pytest.mark.asyncio
async def test_llm_planner_keeps_provider_metadata_when_api_is_selected(monkeypatch):
    class FakeProvider:
        async def complete(self, messages, **kwargs):
            return ProviderResponse(
                text='{"api_id":"resource.status.get","params":{},"confidence":0.8,"reply":"我来查询。"}',
                provider="fake",
                model="planner-v3",
            )

    monkeypatch.setattr("fastaction.planner.llm_planner.build_provider", lambda config: FakeProvider())
    instruction = await LLMPlanner().plan(
        ChatRequest(
            text="查一下当前状态",
            context={"current_resource": {"id": "res_001"}},
        ),
        [make_api()],
        make_provider_config(),
    )

    assert instruction.action == "invoke_api"
    assert instruction.api.id == "resource.status.get"
    assert instruction.provider.id == "fake-answer-provider"
    assert instruction.provider.model == "fake-model"
    assert instruction.provider.runtime_model == "planner-v3"


@pytest.mark.asyncio
async def test_llm_planner_uses_fixed_fallback_when_configured(monkeypatch):
    def fail_if_called(config):
        raise AssertionError("provider should not be called in fixed no-api-hit mode")

    monkeypatch.setattr("fastaction.planner.llm_planner.build_provider", fail_if_called)
    instruction = await LLMPlanner().plan(
        ChatRequest(text="随便聊聊", no_api_hit_strategy="fixed"),
        [],
        make_provider_config(),
    )

    assert instruction.action == "reject"
    assert instruction.reply["zh"] == "当前没有可执行的已注册能力。"


@pytest.mark.asyncio
async def test_llm_planner_hybrid_falls_back_when_answer_provider_fails(monkeypatch):
    class FailingProvider:
        async def complete(self, messages, **kwargs):
            raise ProviderError("timeout")

    monkeypatch.setattr(
        "fastaction.planner.llm_planner.build_provider",
        lambda config: FailingProvider(),
    )
    instruction = await LLMPlanner().plan(
        ChatRequest(text="随便聊聊", no_api_hit_strategy="hybrid"),
        [],
        make_provider_config(),
    )

    assert instruction.action == "reject"
    assert "已回退到确定性规划" in instruction.decision_reason["zh"]


def make_provider_config():
    return ProviderConfig(
        id="fake-answer-provider",
        provider="openai_compatible",
        base_url="https://example.test/v1",
        model="fake-model",
        credentials={"api_key": "test"},
    )
