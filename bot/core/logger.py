"""
Structured logging configuration for the trading bot.

Provides a centralized logger with:
- Console output (human-readable)
- Rotating file output (structured JSON-like format)
- Configurable log levels
- Automatic log directory creation
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

_LOG_DIR = Path(__file__).resolve().parent.parent.parent / "logs"
_LOG_FILE = _LOG_DIR / "trading_bot.log"

_MAX_BYTES = 5 * 1024 * 1024  # 5 MB
_BACKUP_COUNT = 5

_CONSOLE_FORMAT = "%(asctime)s │ %(levelname)-8s │ %(name)-25s │ %(message)s"
_FILE_FORMAT = (
    '{"timestamp":"%(asctime)s","level":"%(levelname)s",'
    '"logger":"%(name)s","message":"%(message)s"}'
)
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

_initialized = False


def setup_logging(level: int = logging.INFO) -> None:
    """
    Initialize the logging subsystem.

    Idempotent — safe to call multiple times. Only the first call
    attaches handlers to the root trading-bot logger.

    Args:
        level: Minimum log level for both console and file handlers.
    """
    global _initialized
    if _initialized:
        return

    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger("bot")
    root_logger.setLevel(level)
    root_logger.propagate = False

    # Console handler — human-readable
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(logging.Formatter(_CONSOLE_FORMAT, datefmt=_DATE_FORMAT))
    root_logger.addHandler(console_handler)

    # File handler — structured, rotating
    file_handler = RotatingFileHandler(
        filename=str(_LOG_FILE),
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(logging.Formatter(_FILE_FORMAT, datefmt=_DATE_FORMAT))
    root_logger.addHandler(file_handler)

    _initialized = True
    root_logger.info("Logging subsystem initialized — log file: %s", _LOG_FILE)


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger under the ``bot`` namespace.

    Args:
        name: Logical module name (e.g. ``exchange.futures``).

    Returns:
        A configured :class:`logging.Logger` instance.
    """
    setup_logging()
    return logging.getLogger(f"bot.{name}")
