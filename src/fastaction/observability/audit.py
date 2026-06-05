from __future__ import annotations

from threading import RLock

from fastaction.schemas import RunRecord
from fastaction.logging import get_logger

logger = get_logger("fastaction.audit")


class AuditRecorder:
    def __init__(self):
        self._runs: list[RunRecord] = []
        self._lock = RLock()

    def record_run(self, run: RunRecord) -> RunRecord:
        with self._lock:
            self._runs.append(run)
        logger.info(
            "fastaction.run_recorded",
            run_id=run.id,
            host_app=run.host_app,
            selected_api_id=run.selected_api_id,
            status=run.status,
            confidence=run.confidence,
        )
        try:
            from fastaction.persistence import persist_run_record

            persist_run_record(run)
        except Exception as exc:
            logger.warning("fastaction.run_persist_failed", run_id=run.id, error=str(exc)[:300])
        return run

    def list_runs(self, limit: int = 100) -> list[RunRecord]:
        with self._lock:
            return list(reversed(self._runs[-limit:]))

    def clear(self) -> None:
        with self._lock:
            self._runs.clear()


audit_recorder = AuditRecorder()
