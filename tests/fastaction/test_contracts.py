from fastaction.domain.enums import OperationType, RiskLevel
from fastaction.schemas import APIDefinition, CardBinding, CardDefinition


def test_api_definition_contract_accepts_resource_schema():
    definition = APIDefinition(
        id="resource.status.get",
        name={"zh": "查询资源状态", "en": "Get resource status"},
        operation_type=OperationType.DETAIL,
        intent={
            "description": "status",
            "examples": {"zh": ["查状态"]},
            "keywords": {"zh": ["状态"]},
        },
        request={
            "method": "get",
            "endpoint": "/api/v1/resources/{resourceId}/status",
        },
        parameters={
            "type": "object",
            "required": ["resourceId"],
            "properties": {
                "resourceId": {
                    "type": "string",
                    "source": ["context.current_resource.id", "clarify"],
                }
            },
        },
        policy={"risk": RiskLevel.READ, "permissions": ["resource:read"]},
    )

    assert definition.request.method == "GET"
    assert definition.required_parameters == ["resourceId"]
    assert definition.parameter_sources("resourceId") == [
        "context.current_resource.id",
        "clarify",
    ]


def test_card_definition_and_binding_contracts():
    card = CardDefinition(card_type="list_card", name={"zh": "列表卡", "en": "List card"})
    binding = CardBinding(
        host_app="example",
        card_type=card.card_type,
        component_key="ResourceListCard",
        field_bindings={"title": "$.name"},
    )

    assert card.states == ["loading", "success", "empty", "error"]
    assert binding.field_bindings["title"] == "$.name"
