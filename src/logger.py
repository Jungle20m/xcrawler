import logging
import os
from logging.handlers import TimedRotatingFileHandler

# Configuration constants
APP_NAME = "alphy"
LOG_DIR = "logs"
LOG_FILE = "app.log"
FORMATTER = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

class Logger:
    _instance = None

    def __new__(cls):
        """Ensure only one instance of Logger is created (Singleton Pattern)."""
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            cls._instance._initialize_logger()
        return cls._instance

    def _initialize_logger(self):
        """Initialize logger with configuration."""
        # Create logger
        self._logger = logging.getLogger(APP_NAME)
        self._logger.setLevel(logging.DEBUG)

        # Create logs directory if it doesn't exist
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR)

        # Create file handler with daily rotation
        log_path = os.path.join(LOG_DIR, LOG_FILE)
        file_handler = TimedRotatingFileHandler(
            log_path, when="midnight", interval=1, backupCount=30
        )
        file_handler.setLevel(logging.DEBUG)

        # Set formatter
        formatter = logging.Formatter(FORMATTER)
        file_handler.setFormatter(formatter)

        # Add handler to logger (check to avoid duplicate handlers)
        if not self._logger.handlers:
            self._logger.addHandler(file_handler)

    def debug(self, msg, *args, **kwargs):
        """Wrapper for debug method."""
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Wrapper for info method."""
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Wrapper for warning method."""
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Wrapper for error method."""
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Wrapper for critical method."""
        self._logger.critical(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        """Wrapper for exception method."""
        self._logger.exception(msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        """Wrapper for log method with custom level."""
        self._logger.log(level, msg, *args, **kwargs)