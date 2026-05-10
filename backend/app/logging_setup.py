"""Root logging: console and optional daily file rotation."""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from notebooklm_shared.config import settings


def _argv_has_celery_worker() -> bool:
    """True when this process was started as ``celery ... worker``."""
    lowered = [a.lower() for a in sys.argv]
    try:
        celery_i = lowered.index("celery")
        worker_i = lowered.index("worker")
    except ValueError:
        return False
    return celery_i < worker_i


def _windows_celery_log_file_name(file_name: str) -> str:
    """Use a separate log file so rotation can rename on Windows.

    ``TimedRotatingFileHandler`` rotates by ``os.rename``. On Windows that
    fails if another process (e.g. the API server) still has the same path
    open, or if multiple prefork children each attach a file handler.
    """
    path = Path(file_name)
    stem = path.stem
    suffix = path.suffix or ".log"
    return f"{stem}-celery{suffix}"


def configure_logging() -> None:
    """Configure the root logger once per process.

    When ``settings.log_dir`` is set, writes to ``<log_dir>/<log_file_name>``,
    rotates at local midnight, and names rolled files with a ``.YYYY-MM-DD``
    suffix.
    Set ``LOG_FILE_BACKUP_COUNT=0`` to never delete old daily files.
    """
    root = logging.getLogger()
    if getattr(root, "_notebooklm_logging_configured", False):
        return

    level_name = (settings.log_level or "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    root.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if settings.log_to_console:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(level)
        stream_handler.setFormatter(formatter)
        root.addHandler(stream_handler)

    log_dir = (settings.log_dir or "").strip()
    if log_dir:
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        file_name = (settings.log_file_name or "app.log").strip() or "app.log"
        if sys.platform == "win32" and _argv_has_celery_worker():
            file_name = _windows_celery_log_file_name(file_name)
        file_handler = TimedRotatingFileHandler(
            filename=str(log_path / file_name),
            when="midnight",
            interval=1,
            backupCount=settings.log_file_backup_count,
            encoding="utf-8",
            utc=False,
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)

    root._notebooklm_logging_configured = True  # type: ignore[attr-defined]
