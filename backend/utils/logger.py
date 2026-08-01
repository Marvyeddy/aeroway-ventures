from __future__ import annotations

import logging
from logging.handlers import TimedRotatingFileHandler
import sys

DEFAULT_LOG_FILE = "backend.log"
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s | %(levelname)s | %(name)s | %(lineno)d | %(message)s"


class LogManager:
    _instance: "LogManager" | None = None
    _logger: dict[str, logging.Logger] = {}

    def __new__(cls, *args, **kwargs) -> "LogManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._configure_root_logger()
        return cls._instance

    def _configure_root_logger(self) -> None:
        root_logger = logging.getLogger()
        root_logger.setLevel(DEFAULT_LOG_LEVEL)
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

        if not any(
            isinstance(handler, logging.StreamHandler)
            for handler in root_logger.handlers
        ):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            root_logger.addHandler(console_handler)

        if not any(
            isinstance(handler, TimedRotatingFileHandler)
            for handler in root_logger.handlers
        ):
            file_handler = TimedRotatingFileHandler(
                filename=DEFAULT_LOG_FILE,
                when="midnight",
                interval=1,
                backupCount=7,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)

    def get_loggers(self, name: str) -> logging.Logger:
        if name not in self._logger:
            logger = logging.getLogger(name)
            logger.setLevel(DEFAULT_LOG_LEVEL)
            self._logger[name] = logger

        return self._logger[name]


log_manager = LogManager()


def get_app_logger(name: str = __name__) -> logging.Logger:
    return log_manager.get_loggers(name)
