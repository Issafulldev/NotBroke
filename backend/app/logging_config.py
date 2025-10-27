"""Logging configuration for audit trail and security events."""

import logging
import json
from datetime import datetime

def setup_audit_logger():
    """Configure structured JSON logging for security audit."""
    
    logger = logging.getLogger("audit")
    
    # Only add handlers if they don't exist
    if logger.hasHandlers():
        return logger
    
    logger.setLevel(logging.INFO)
    
    # Simple JSON formatter
    class JSONFormatter(logging.Formatter):
        def format(self, record):
            log_obj = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
            }
            if hasattr(record, 'audit_data'):
                log_obj.update(record.audit_data)
            return json.dumps(log_obj)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File handler (audit trail)
    try:
        file_handler = logging.FileHandler("audit.log")
        file_handler.setFormatter(JSONFormatter())
        logger.addHandler(file_handler)
    except Exception:
        # If file handler fails, just use console
        pass
    
    return logger


AUDIT_LOGGER = setup_audit_logger()


def log_security_event(event_type: str, user_id: int | None = None, details: dict | None = None):
    """Log security events to audit trail."""
    audit_data = {
        "event_type": event_type,
        "user_id": user_id,
    }
    if details:
        audit_data.update(details)
    
    record = logging.LogRecord(
        name="audit",
        level=logging.INFO,
        pathname="",
        lineno=0,
        msg=event_type,
        args=(),
        exc_info=None,
    )
    record.audit_data = audit_data
    AUDIT_LOGGER.handle(record)
