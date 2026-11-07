"""Configuração central de logging do MainERP."""

import logging
from logging.handlers import RotatingFileHandler

import paths

_HANDLER_NAME = "mainerp_file"
_MAX_BYTES = 5 * 1024 * 1024
_BACKUP_COUNT = 5
_FORMAT = "%(asctime)s %(levelname)s [%(name)s] %(message)s"


def configurar_logging() -> None:
    """Registra os logs da aplicação em dados/logs/sistema.log."""
    root_logger = logging.getLogger()
    if any(handler.get_name() == _HANDLER_NAME for handler in root_logger.handlers):
        return

    log_dir = paths.DATA_DIR / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_dir / "sistema.log",
        maxBytes=_MAX_BYTES,
        backupCount=_BACKUP_COUNT,
        encoding="utf-8",
    )
    handler.set_name(_HANDLER_NAME)
    handler.setFormatter(logging.Formatter(_FORMAT))

    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(handler)
