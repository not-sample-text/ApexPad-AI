import logging
import threading
import time
from collections import deque
from typing import Any

MAX_LOG_ENTRIES = 300

_log_lock = threading.Lock()
_log_buffer: deque[dict[str, Any]] = deque(maxlen=MAX_LOG_ENTRIES)
_log_counter = 0


class RingBufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        global _log_counter
        try:
            msg = self.format(record)
            with _log_lock:
                _log_counter += 1
                _log_buffer.append({
                    "id": _log_counter,
                    "timestamp": time.strftime("%H:%M:%S"),
                    "level": record.levelname,
                    "name": record.name,
                    "message": msg
                })
        except Exception:
            self.handleError(record)


def get_logs_since(last_id: int = 0) -> list[dict[str, Any]]:
    with _log_lock:
        return [entry for entry in _log_buffer if entry["id"] > last_id]


def clear_logs() -> None:
    with _log_lock:
        _log_buffer.clear()


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)

        formatter = logging.Formatter('[%(levelname)s] %(name)s: %(message)s')

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        rbh = RingBufferHandler()
        rbh.setLevel(logging.DEBUG)
        rbh.setFormatter(formatter)
        logger.addHandler(rbh)

    return logger
