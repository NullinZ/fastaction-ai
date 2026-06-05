from __future__ import annotations

from typing import Any


def read_path(data: Any, path: str) -> Any:
    """Read a minimal JSONPath-like path: $, $.a.b, $.items.0.name."""
    if path in ("", "$"):
        return data
    if not path.startswith("$."):
        return None
    current = data
    for part in path[2:].split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            index = int(part)
            current = current[index] if index < len(current) else None
        else:
            return None
    return current


def write_path(target: dict[str, Any], path: str, value: Any) -> None:
    if not path:
        return
    parts = path.split(".")
    current = target
    for part in parts[:-1]:
        existing = current.get(part)
        if not isinstance(existing, dict):
            existing = {}
            current[part] = existing
        current = existing
    current[parts[-1]] = value


def apply_field_bindings(data: Any, bindings: dict[str, str]) -> dict[str, Any]:
    props: dict[str, Any] = {}
    for target_path, source_path in bindings.items():
        value = read_path(data, source_path) if source_path.startswith("$") else source_path
        write_path(props, target_path, value)
    return props
