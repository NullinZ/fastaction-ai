from __future__ import annotations

from typing import Any, Literal

from pydantic import Field, field_validator, model_validator

from fastaction.domain.enums import AuthMode, OperationType, RiskLevel
from fastaction.schemas.common import FastActionModel, IntentDefinition, JsonObject, LocalizedText

AuthPlacement = Literal["header", "query", "cookie", "transport", "none"]
APIExecutionMode = Literal["none", "host_executor", "manual"]


class APIAuthDefinition(FastActionModel):
    mode: AuthMode | None = None
    placement: AuthPlacement = "header"
    scheme: str = "Bearer"
    header_name: str | None = None
    query_name: str | None = None
    cookie_name: str | None = None
    token_context_path: str | None = None
    secret_ref: str | None = None
    client_id_ref: str | None = None
    client_secret_ref: str | None = None
    token_url: str | None = None
    scopes: list[str] = Field(default_factory=list)
    username_ref: str | None = None
    password_ref: str | None = None
    certificate_ref: str | None = None
    private_key_ref: str | None = None
    custom_header_refs: dict[str, str] = Field(default_factory=dict)
    metadata: JsonObject = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_mode_shape(self):
        _validate_auth_shape(self.mode, self)
        return self


class APIRequestDefinition(FastActionModel):
    method: str = Field("GET", max_length=20)
    endpoint: str = Field(..., min_length=1, max_length=800)
    auth_mode: AuthMode = AuthMode.USER_TOKEN
    auth: APIAuthDefinition = Field(default_factory=APIAuthDefinition)
    timeout_ms: int = Field(10000, ge=100, le=300000)
    retry: JsonObject = Field(default_factory=lambda: {"enabled": False, "max_attempts": 0})

    @field_validator("method")
    @classmethod
    def normalize_method(cls, value: str) -> str:
        return value.upper()

    @property
    def effective_auth_mode(self) -> AuthMode | str:
        return self.auth.mode or self.auth_mode

    @model_validator(mode="after")
    def validate_effective_auth_shape(self):
        _validate_auth_shape(self.effective_auth_mode, self.auth)
        return self


def _validate_auth_shape(mode: AuthMode | str | None, auth: APIAuthDefinition) -> None:
    if mode is None:
        return
    if mode in (AuthMode.SERVICE_TOKEN, AuthMode.BEARER_TOKEN) and not auth.secret_ref:
        raise ValueError(f"{mode} auth requires secret_ref")
    if mode == AuthMode.API_KEY and not auth.secret_ref:
        raise ValueError("api_key auth requires secret_ref")
    if mode == AuthMode.API_KEY and auth.placement == "header" and not auth.header_name:
        raise ValueError("api_key header auth requires header_name")
    if mode == AuthMode.API_KEY and auth.placement == "query" and not auth.query_name:
        raise ValueError("api_key query auth requires query_name")
    if mode == AuthMode.API_KEY and auth.placement == "cookie" and not auth.cookie_name:
        raise ValueError("api_key cookie auth requires cookie_name")
    if mode == AuthMode.OAUTH2_CLIENT_CREDENTIALS and not (
        auth.token_url and auth.client_id_ref and auth.client_secret_ref
    ):
        raise ValueError(
            "oauth2_client_credentials auth requires token_url, client_id_ref, and client_secret_ref"
        )
    if mode == AuthMode.BASIC and not (auth.username_ref and auth.password_ref):
        raise ValueError("basic auth requires username_ref and password_ref")
    if mode == AuthMode.CUSTOM_HEADER and not auth.custom_header_refs:
        raise ValueError("custom_header auth requires custom_header_refs")
    if mode == AuthMode.MTLS and not (auth.certificate_ref and auth.private_key_ref):
        raise ValueError("mtls auth requires certificate_ref and private_key_ref")


class APIResponseDefinition(FastActionModel):
    data_path: str = "$"
    exposed_fields: list[str] = Field(default_factory=list)
    sensitive_fields: list[str] = Field(default_factory=list)
    prompt_visible_fields: list[str] = Field(default_factory=list)
    log_redaction: list[str] = Field(default_factory=list)


class APIPolicyDefinition(FastActionModel):
    risk: RiskLevel = RiskLevel.READ
    requires_confirmation: bool | str = False
    permissions: list[str] = Field(default_factory=list)
    idempotency: str = "unknown"


class APIRenderDefinition(FastActionModel):
    card_type: str = "generic_data_card"
    fallback_card_type: str = "generic_data_card"
    field_bindings: dict[str, str] = Field(default_factory=dict)


class APIExecutionDefinition(FastActionModel):
    mode: APIExecutionMode = "none"
    executor_id: str | None = None
    requires_confirmation: bool | None = None
    input_mapping: JsonObject = Field(default_factory=dict)
    endpoints: JsonObject = Field(default_factory=dict)
    metadata: JsonObject = Field(default_factory=dict)


class APIDefinition(FastActionModel):
    id: str = Field(..., min_length=1, max_length=160)
    name: LocalizedText
    version: str = "1.0.0"
    status: str = "active"
    operation_type: OperationType
    intent: IntentDefinition
    request: APIRequestDefinition
    parameters: JsonObject = Field(default_factory=lambda: {"type": "object", "properties": {}})
    response: APIResponseDefinition = Field(default_factory=APIResponseDefinition)
    policy: APIPolicyDefinition = Field(default_factory=APIPolicyDefinition)
    render: APIRenderDefinition = Field(default_factory=APIRenderDefinition)
    execution: APIExecutionDefinition = Field(default_factory=APIExecutionDefinition)
    metadata: dict[str, Any] = Field(default_factory=dict)

    @field_validator("id")
    @classmethod
    def normalize_id(cls, value: str) -> str:
        return value.strip()

    @property
    def required_parameters(self) -> list[str]:
        required = self.parameters.get("required", [])
        return [str(item) for item in required] if isinstance(required, list) else []

    def parameter_sources(self, parameter_name: str) -> list[str]:
        properties = self.parameters.get("properties", {})
        if not isinstance(properties, dict):
            return []
        definition = properties.get(parameter_name, {})
        if not isinstance(definition, dict):
            return []
        source = definition.get("source", [])
        if isinstance(source, str):
            return [source]
        if isinstance(source, list):
            return [str(item) for item in source]
        return []
