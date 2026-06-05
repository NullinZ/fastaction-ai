import pytest
from pydantic import ValidationError

from fastaction.domain.enums import OperationType
from fastaction.executor import build_auth_parts, describe_auth_requirements
from fastaction.schemas import APIDefinition


def make_definition(request_auth):
    return APIDefinition(
        id="external.items.list",
        name={"zh": "查询外部条目", "en": "List external items"},
        operation_type=OperationType.LIST,
        intent={"examples": ["查条目"], "keywords": ["条目"]},
        request={
            "method": "GET",
            "endpoint": "/external/items",
            "auth": request_auth,
        },
    )


def test_api_key_auth_registration_and_resolution():
    definition = make_definition(
        {
            "mode": "api_key",
            "placement": "header",
            "header_name": "X-API-Key",
            "secret_ref": "host.external_api_key",
        }
    )

    assert definition.request.effective_auth_mode == "api_key"
    assert describe_auth_requirements(definition.request)["secret_refs"] == [
        "host.external_api_key"
    ]
    assert build_auth_parts(
        definition.request,
        secrets={"host.external_api_key": "test-key"},
    )["headers"] == {"X-API-Key": "test-key"}


def test_user_token_auth_resolution_uses_host_context():
    definition = make_definition({"mode": "user_token"})

    parts = build_auth_parts(
        definition.request,
        context={"auth": {"access_token": "user-jwt"}},
    )

    assert parts["headers"] == {"Authorization": "Bearer user-jwt"}


def test_oauth2_client_credentials_requires_token_registration_fields():
    with pytest.raises(ValidationError):
        make_definition({"mode": "oauth2_client_credentials", "token_url": "/oauth/token"})


def test_auth_mode_alias_still_requires_matching_auth_config():
    with pytest.raises(ValidationError):
        APIDefinition(
            id="external.items.list",
            name={"zh": "查询外部条目", "en": "List external items"},
            operation_type=OperationType.LIST,
            intent={"examples": ["查条目"], "keywords": ["条目"]},
            request={
                "method": "GET",
                "endpoint": "/external/items",
                "auth_mode": "api_key",
            },
        )
