from __future__ import annotations

import logging
from typing import Any


class StructuredLogger:
    def __init__(self, name: str):
        self._logger = logging.getLogger(name)

    def info(self, message: str, **fields: Any) -> None:
        self._log(logging.INFO, message, fields)

    def warning(self, message: str, **fields: Any) -> None:
        self._log(logging.WARNING, message, fields)

    def error(self, message: str, **fields: Any) -> None:
        self._log(logging.ERROR, message, fields)

    def debug(self, message: str, **fields: Any) -> None:
        self._log(logging.DEBUG, message, fields)

    def _log(self, level: int, message: str, fields: dict[str, Any]) -> None:
        if fields:
            self._logger.log(level, "%s %s", message, fields)
        else:
            self._logger.log(level, "%s", message)


def get_logger(name: str) -> StructuredLogger:
    logging.basicConfig(level=logging.INFO)
    return StructuredLogger(name)

