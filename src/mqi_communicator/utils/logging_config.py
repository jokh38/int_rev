import logging
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """
    Formats log records into a JSON string.
    """
    def format(self, record: logging.LogRecord) -> str:
        log_object = {
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger_name": record.name,
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }
        # Add extra fields if they exist
        if hasattr(record, 'extra_info'):
            log_object.update(record.extra_info)

        return json.dumps(log_object)

def setup_logging(level=logging.INFO):
    """
    Configures the root logger for structured JSON logging.
    """
    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create a new handler that streams to stdout
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    logger.addHandler(handler)
