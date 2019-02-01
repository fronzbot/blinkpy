"""Module for blinkpy logging."""
import logging


def create_logger(name):
    """Create a logger instance."""
    handler = RepeatLogHandler()
    handler.setFormatter(log_formatter())
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)
    return logger


def log_formatter():
    """Create log formatter."""
    fmt = "%(asctime)s %(levelname)s [%(name)s] %(message)s"
    return logging.Formatter(fmt)


class RepeatLogHandler(logging.StreamHandler):
    """Log handler for repeat entries."""

    def __init__(self):
        """Initialize repeat log handler."""
        super().__init__()
        self.log_record = set()

    def emit(self, record):
        """Ensure we only log a message once."""
        if record.msg not in self.log_record:
            self.log_record.add(record.msg)
            super().emit(record)
