import logging
import logging.config
import os
from contextvars import ContextVar

# ContextVar to store request_id per-thread/async-task context
request_id_ctx: ContextVar[str] = ContextVar("request_id", default="-")

class RequestIdFilter(logging.Filter):
    """Filter to inject request_id into each log record."""
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True

def setup_logging():
    """Setup logging configuration."""
    # Ensure logs directory exists
    os.makedirs("logs", exist_ok=True)

    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {
                "()": RequestIdFilter,
            }
        },
        "formatters": {
            "standard": {
                "format": "%(asctime)s [%(levelname)s] [%(request_id)s] %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": "INFO",
                "formatter": "standard",
                "filters": ["request_id"],
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": "INFO",
                "filename": "logs/app.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
                "formatter": "standard",
                "filters": ["request_id"],
                "encoding": "utf8",
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": "INFO",
        },
    }

    logging.config.dictConfig(log_config)
