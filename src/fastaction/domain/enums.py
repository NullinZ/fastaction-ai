from __future__ import annotations

from enum import StrEnum


class OperationType(StrEnum):
    LIST = "list"
    DETAIL = "detail"
    COUNT = "count"
    AGGREGATE = "aggregate"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ACTION = "action"
    WORKFLOW = "workflow"


class RiskLevel(StrEnum):
    READ = "read"
    WRITE = "write"
    DESTRUCTIVE = "destructive"
    EXTERNAL = "external"


class InstructionAction(StrEnum):
    INVOKE_API = "invoke_api"
    CLARIFY = "clarify"
    CONFIRM = "confirm"
    ANSWER = "answer"
    HYBRID = "hybrid"
    REJECT = "reject"


class NoApiHitStrategy(StrEnum):
    FIXED = "fixed"
    LLM_ANSWER = "llm_answer"
    HYBRID = "hybrid"


class ResultStatus(StrEnum):
    SUCCESS = "success"
    EMPTY = "empty"
    ERROR = "error"
    FORBIDDEN = "forbidden"
    TIMEOUT = "timeout"


class ProviderType(StrEnum):
    LLM = "llm"
    EMBEDDING = "embedding"
    ASR = "asr"
    RERANK = "rerank"


class ProviderKind(StrEnum):
    OPENAI = "openai"
    OPENAI_COMPATIBLE = "openai_compatible"
    ANTHROPIC = "anthropic"
    QWEN = "qwen"
    DOUBAO = "doubao"
    MIMO = "mimo"
    DEEPSEEK = "deepseek"


class AuthMode(StrEnum):
    USER_TOKEN = "user_token"
    USER_COOKIE = "user_cookie"
    SERVICE_TOKEN = "service_token"
    BEARER_TOKEN = "bearer_token"
    API_KEY = "api_key"
    OAUTH2_CLIENT_CREDENTIALS = "oauth2_client_credentials"
    BASIC = "basic"
    CUSTOM_HEADER = "custom_header"
    MTLS = "mtls"
    HOST_PROXY = "host_proxy"
    NONE = "none"
