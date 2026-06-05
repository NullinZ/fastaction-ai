from __future__ import annotations

from base64 import b64encode
from typing import Any

from fastaction.domain.enums import AuthMode
from fastaction.schemas.api_definition import APIRequestDefinition


class AuthResolutionError(ValueError):
    pass


def describe_auth_requirements(request: APIRequestDefinition) -> dict[str, Any]:
    auth = request.auth
    mode = auth.mode or request.auth_mode
    secret_refs: list[str] = []
    for ref in (
        auth.secret_ref,
        auth.client_id_ref,
        auth.client_secret_ref,
        auth.username_ref,
        auth.password_ref,
        auth.certificate_ref,
        auth.private_key_ref,
    ):
        if ref:
            secret_refs.append(ref)
    secret_refs.extend(auth.custom_header_refs.values())
    return {
        "mode": mode,
        "placement": auth.placement,
        "secret_refs": sorted(set(secret_refs)),
        "uses_user_context": mode in (AuthMode.USER_TOKEN, AuthMode.USER_COOKIE),
        "uses_host_proxy": mode == AuthMode.HOST_PROXY,
    }


def build_auth_parts(
    request: APIRequestDefinition,
    *,
    context: dict[str, Any] | None = None,
    secrets: dict[str, str] | None = None,
) -> dict[str, Any]:
    auth = request.auth
    mode = auth.mode or request.auth_mode
    context = context or {}
    secrets = secrets or {}
    parts: dict[str, Any] = {"headers": {}, "query": {}, "cookies": {}, "transport": {}}

    if mode in (AuthMode.NONE, AuthMode.HOST_PROXY):
        return parts

    if mode == AuthMode.USER_TOKEN:
        token = _read_context(context, auth.token_context_path or "$.auth.access_token")
        if not token:
            token = _read_context(context, "$.auth.authorization")
        if not token:
            raise AuthResolutionError("user_token auth requires auth.access_token or auth.authorization")
        parts["headers"][auth.header_name or "Authorization"] = _bearer_value(str(token), auth.scheme)
        return parts

    if mode == AuthMode.USER_COOKIE:
        cookie_name = auth.cookie_name or "session"
        cookie_value = _read_context(context, auth.token_context_path or f"$.auth.cookies.{cookie_name}")
        if not cookie_value:
            raise AuthResolutionError(f"user_cookie auth requires context value for {cookie_name}")
        parts["cookies"][cookie_name] = str(cookie_value)
        return parts

    if mode in (AuthMode.SERVICE_TOKEN, AuthMode.BEARER_TOKEN):
        token = _read_secret(auth.secret_ref, secrets)
        parts["headers"][auth.header_name or "Authorization"] = _bearer_value(token, auth.scheme)
        return parts

    if mode == AuthMode.API_KEY:
        value = _read_secret(auth.secret_ref, secrets)
        if auth.placement == "header":
            parts["headers"][_required(auth.header_name, "api_key header_name")] = value
        elif auth.placement == "query":
            parts["query"][_required(auth.query_name, "api_key query_name")] = value
        elif auth.placement == "cookie":
            parts["cookies"][_required(auth.cookie_name, "api_key cookie_name")] = value
        else:
            raise AuthResolutionError("api_key auth supports header, query, or cookie placement")
        return parts

    if mode == AuthMode.BASIC:
        username = _read_secret(auth.username_ref, secrets)
        password = _read_secret(auth.password_ref, secrets)
        basic = b64encode(f"{username}:{password}".encode("utf-8")).decode("ascii")
        parts["headers"][auth.header_name or "Authorization"] = f"Basic {basic}"
        return parts

    if mode == AuthMode.CUSTOM_HEADER:
        for header_name, secret_ref in auth.custom_header_refs.items():
            parts["headers"][header_name] = _read_secret(secret_ref, secrets)
        return parts

    if mode == AuthMode.OAUTH2_CLIENT_CREDENTIALS:
        cached_token = _read_context(context, auth.token_context_path or "")
        if cached_token:
            parts["headers"][auth.header_name or "Authorization"] = _bearer_value(
                str(cached_token), auth.scheme
            )
            return parts
        parts["oauth2"] = {
            "grant_type": "client_credentials",
            "token_url": auth.token_url,
            "client_id_ref": auth.client_id_ref,
            "client_secret_ref": auth.client_secret_ref,
            "scopes": auth.scopes,
            "requires_token_exchange": True,
        }
        return parts

    if mode == AuthMode.MTLS:
        parts["transport"] = {
            "certificate_ref": auth.certificate_ref,
            "private_key_ref": auth.private_key_ref,
        }
        return parts

    raise AuthResolutionError(f"unsupported auth mode: {mode}")


def _bearer_value(token: str, scheme: str) -> str:
    if token.lower().startswith(("bearer ", "basic ")):
        return token
    return f"{scheme} {token}".strip()


def _read_secret(ref: str | None, secrets: dict[str, str]) -> str:
    if not ref:
        raise AuthResolutionError("auth secret_ref is required")
    if ref not in secrets:
        raise AuthResolutionError(f"missing auth secret: {ref}")
    return str(secrets[ref])


def _read_context(context: dict[str, Any], path: str) -> Any:
    if not path:
        return None
    normalized = path[2:] if path.startswith("$.") else path
    current: Any = context
    for part in normalized.split("."):
        if not part:
            continue
        if isinstance(current, dict):
            current = current.get(part)
            continue
        return None
    return current


def _required(value: str | None, name: str) -> str:
    if not value:
        raise AuthResolutionError(f"{name} is required")
    return value
