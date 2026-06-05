from __future__ import annotations

from threading import RLock
from typing import Generic, TypeVar

from fastaction.domain.errors import RegistryNotFoundError

T = TypeVar("T")


class InMemoryRegistry(Generic[T]):
    def __init__(self, id_getter):
        self._items: dict[str, T] = {}
        self._id_getter = id_getter
        self._lock = RLock()

    def list(self) -> list[T]:
        with self._lock:
            return list(self._items.values())

    def get(self, item_id: str) -> T:
        with self._lock:
            try:
                return self._items[item_id]
            except KeyError as exc:
                raise RegistryNotFoundError(f"registry item not found: {item_id}") from exc

    def upsert(self, item: T) -> T:
        item_id = self._id_getter(item)
        with self._lock:
            self._items[item_id] = item
        return item

    def delete(self, item_id: str) -> None:
        with self._lock:
            if item_id not in self._items:
                raise RegistryNotFoundError(f"registry item not found: {item_id}")
            del self._items[item_id]

    def clear(self) -> None:
        with self._lock:
            self._items.clear()
