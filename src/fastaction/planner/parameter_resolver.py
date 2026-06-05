from __future__ import annotations

from typing import Any

from fastaction.executor.field_mapper import read_path
from fastaction.schemas import APIDefinition


class ParameterResolver:
    def resolve(
        self,
        api: APIDefinition,
        *,
        context: dict[str, Any],
        provided_params: dict[str, Any],
        text: str = "",
    ) -> tuple[dict[str, Any], list[str]]:
        params: dict[str, Any] = {}
        missing: list[str] = []
        properties = api.parameters.get("properties", {})
        if not isinstance(properties, dict):
            properties = {}
        required_names = set(api.required_parameters)

        for name in properties:
            value = self._resolve_value(api, name, context, provided_params, text)
            if value is None:
                if name in required_names:
                    missing.append(name)
                continue
            params[name] = value

        for name, value in provided_params.items():
            if value is not None and name not in params:
                params[name] = value

        return params, missing

    def _resolve_value(
        self,
        api: APIDefinition,
        parameter_name: str,
        context: dict[str, Any],
        provided_params: dict[str, Any],
        text: str,
    ) -> Any:
        value = provided_params.get(parameter_name)
        if value is not None:
            return value
        value = self._from_sources(api.parameter_sources(parameter_name), context, provided_params)
        if value is not None:
            return value
        definition = api.parameters.get("properties", {}).get(parameter_name, {})
        if isinstance(definition, dict):
            value = self._from_text_aliases(definition, text)
            if value is not None:
                return value
        if isinstance(definition, dict) and "default" in definition:
            return definition["default"]
        return None

    def _from_sources(
        self,
        sources: list[str],
        context: dict[str, Any],
        provided_params: dict[str, Any],
    ) -> Any:
        for source in sources:
            if source == "user_input" or source == "clarify":
                continue
            if source.startswith("context."):
                value = read_path({"context": context}, f"$.{source}")
                if value is not None:
                    return value
            if source.startswith("params."):
                value = read_path({"params": provided_params}, f"$.{source}")
                if value is not None:
                    return value
        return None

    def _from_text_aliases(self, definition: dict[str, Any], text: str) -> Any:
        aliases = definition.get("text_aliases")
        if not isinstance(aliases, dict) or not text:
            return None
        normalized_text = _compact_text(text).lower()
        for value, patterns in aliases.items():
            if isinstance(patterns, str):
                patterns = [patterns]
            if not isinstance(patterns, list):
                continue
            for pattern in patterns:
                if not isinstance(pattern, str) or not pattern.strip():
                    continue
                if _compact_text(pattern).lower() in normalized_text:
                    return value
        return None


def _compact_text(value: str) -> str:
    return "".join(char for char in value if not char.isspace())
