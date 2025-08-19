import logging
import sys
import re
from contextvars import ContextVar

request_id_var: ContextVar[str] = ContextVar("request_id", default="N/A")

class PiiRedactingFormatter(logging.Formatter):
    """Custom log formatter to redact PII like customerId from log messages."""
    def format(self, record):
        message = super().format(record)
        message = re.sub(r'("customerId":\s*)"[^"]+"', r'\1"REDACTED"', message)
        return message

def setup_logging():
    """Sets up the root logger."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    formatter = PiiRedactingFormatter(
        "[%(asctime)s] [%(levelname)s] [request_id=%(request_id)s] - %(message)s"
    )

    class RequestIdFilter(logging.Filter):
        def filter(self, record):
            record.request_id = request_id_var.get()
            return True

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    if not logger.handlers:
        logger.addHandler(handler)

logger = logging.getLogger(__name__)