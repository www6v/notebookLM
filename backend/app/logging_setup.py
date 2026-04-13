"""Root logging: console and optional daily file rotation."""

import logging
import sys
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path

from app.config import settings


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
