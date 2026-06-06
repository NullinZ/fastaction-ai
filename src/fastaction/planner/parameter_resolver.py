from __future__ import annotations

from difflib import SequenceMatcher
import re
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
        definition = api.parameters.get("properties", {}).get(parameter_name, {})
        value = provided_params.get(parameter_name)
        if isinstance(definition, dict):
            value = self._normalize_option_value(definition, value)
        if value is not None:
            return value
        if isinstance(definition, dict):
            value = self._from_entity_definition(definition, context, text)
            if value is not None:
                return value
        value = self._from_sources(api.parameter_sources(parameter_name), context, provided_params)
        if isinstance(definition, dict):
            value = self._normalize_option_value(definition, value)
        if value is not None:
            return value
        if isinstance(definition, dict):
            value = self._from_option_set_text(definition, text)
            if value is not None:
                return value
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

    def _from_option_set_text(self, definition: dict[str, Any], text: str) -> Any:
        option_set = _option_set(definition)
        if option_set is None or not text:
            return None
        normalized_text = _compact_text(text).lower()
        for option in option_set.options:
            if not option.is_active:
                continue
            for term in _option_terms(option):
                if _compact_text(term).lower() in normalized_text:
                    return option.value
        return None

    def _normalize_option_value(self, definition: dict[str, Any], value: Any) -> Any:
        option_set = _option_set(definition)
        if option_set is None or value is None:
            return value
        normalized_value = _compact_text(str(value)).lower()
        for option in option_set.options:
            if not option.is_active:
                continue
            for term in _option_terms(option):
                if _compact_text(term).lower() == normalized_value:
                    return option.value
        return value

    def _from_entity_definition(
        self,
        definition: dict[str, Any],
        context: dict[str, Any],
        text: str,
    ) -> Any:
        entity_type = definition.get("resolve_entity")
        if not isinstance(entity_type, str) or not entity_type.strip() or not text:
            return None
        candidates = _entity_candidates(context, entity_type.strip())
        if not candidates:
            return None
        matches: list[tuple[float, int, Any]] = []
        for candidate in candidates:
            entity_id = _entity_id(candidate, entity_type)
            if entity_id is None:
                continue
            score, label_length = _entity_match_score(candidate, text)
            if score >= 0.82:
                matches.append((score, label_length, entity_id))
        if not matches:
            return None
        matches.sort(key=lambda item: (item[0], item[1]), reverse=True)
        if len(matches) > 1 and matches[0][0] < 0.98 and matches[0][0] - matches[1][0] < 0.04:
            return None
        return matches[0][2]


def _compact_text(value: str) -> str:
    return "".join(char for char in value if not char.isspace())


def _option_set(definition: dict[str, Any]):
    option_set_id = definition.get("option_set")
    if not isinstance(option_set_id, str) or not option_set_id.strip():
        return None
    try:
        from fastaction.registries import runtime

        option_set = runtime.option_sets.get(option_set_id.strip())
    except Exception:
        return None
    if not option_set.is_active:
        return None
    return option_set


def _option_terms(option) -> list[str]:
    terms = [option.value]
    if isinstance(option.label, dict):
        terms.extend(str(value) for value in option.label.values() if value is not None)
    elif isinstance(option.label, str):
        terms.append(option.label)
    terms.extend(option.aliases)
    return [term for term in terms if isinstance(term, str) and term.strip()]


def _entity_candidates(context: dict[str, Any], entity_type: str) -> list[Any]:
    plural = _pluralize(entity_type)
    keys = [
        entity_type,
        plural,
        f"{entity_type}_list",
        f"{plural}_list",
        f"available_{entity_type}",
        f"available_{plural}",
        f"accessible_{entity_type}",
        f"accessible_{plural}",
        f"{entity_type}_candidates",
        f"{plural}_candidates",
        f"available_{entity_type}_candidates",
        f"available_{plural}_candidates",
    ]
    result: list[Any] = []
    for key in keys:
        result.extend(_coerce_candidates(context.get(key)))
    for container_key in ("entities", "entity_candidates", "available_entities", "accessible_entities"):
        container = context.get(container_key)
        if isinstance(container, dict):
            for key in (entity_type, plural):
                result.extend(_coerce_candidates(container.get(key)))
    return _dedupe_candidates(result, entity_type)


def _coerce_candidates(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        for key in ("items", "data", "list", "records", "results"):
            nested = value.get(key)
            if isinstance(nested, list):
                return nested
        if "id" in value or "name" in value or "label" in value:
            return [value]
    return []


def _dedupe_candidates(candidates: list[Any], entity_type: str) -> list[Any]:
    seen: set[str] = set()
    result: list[Any] = []
    for candidate in candidates:
        entity_id = _entity_id(candidate, entity_type)
        marker = str(entity_id if entity_id is not None else candidate)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(candidate)
    return result


def _entity_id(candidate: Any, entity_type: str) -> Any:
    if isinstance(candidate, str):
        return candidate
    if not isinstance(candidate, dict):
        return None
    for key in ("id", f"{entity_type}_id", "uuid", "value", "key"):
        value = candidate.get(key)
        if value is not None and str(value).strip():
            return value
    return None


def _entity_match_score(candidate: Any, text: str) -> tuple[float, int]:
    labels = _entity_labels(candidate)
    if not labels:
        return 0.0, 0
    best_score = 0.0
    best_length = 0
    for label in labels:
        compact_label = _normalize_match_text(label)
        compact_text = _normalize_match_text(text)
        if not compact_label:
            continue
        if compact_label in compact_text:
            score = 1.0
        elif _normalize_numeric_zeros(compact_label) in _normalize_numeric_zeros(compact_text):
            score = 0.96
        else:
            score = SequenceMatcher(None, compact_label, compact_text).ratio()
        if score > best_score:
            best_score = score
            best_length = len(compact_label)
    return best_score, best_length


def _entity_labels(candidate: Any) -> list[str]:
    if isinstance(candidate, str):
        return [candidate]
    if not isinstance(candidate, dict):
        return []
    labels: list[str] = []
    for key in (
        "name",
        "label",
        "title",
        "display_name",
        "alias",
        "code",
        "number",
        "short_name",
        "description",
    ):
        value = candidate.get(key)
        if isinstance(value, str) and value.strip():
            labels.append(value)
        elif isinstance(value, list):
            labels.extend(item for item in value if isinstance(item, str) and item.strip())
    for key in ("aliases", "keywords"):
        value = candidate.get(key)
        if isinstance(value, list):
            labels.extend(item for item in value if isinstance(item, str) and item.strip())
    return _dedupe_strings(labels)


def _normalize_match_text(value: str) -> str:
    return re.sub(r"[\s\-_·,，.。:：/\\()（）【】\\[\\]{}]+", "", value).lower()


def _normalize_numeric_zeros(value: str) -> str:
    return re.sub(r"\d+", lambda match: str(int(match.group(0))), value)


def _pluralize(value: str) -> str:
    if value.endswith("y"):
        return f"{value[:-1]}ies"
    if value.endswith("s"):
        return value
    return f"{value}s"


def _dedupe_strings(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        marker = _normalize_match_text(value)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(value)
    return result
