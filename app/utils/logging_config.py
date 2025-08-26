import logging
import logging.config
import structlog
from typing import Any
import json
from datetime import datetime


def setup_logging():
    """Setup structured logging with structlog"""
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=None,
        level=logging.INFO,
    )
    
    # Configure structlog
    structlog.configure(
        processors=[
            # Add timestamp
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            # JSON formatting for production
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields
        for key, value in record.__dict__.items():
            if key not in ('name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 
                          'filename', 'module', 'exc_info', 'exc_text', 'stack_info',
                          'lineno', 'funcName', 'created', 'msecs', 'relativeCreated',
                          'thread', 'threadName', 'processName', 'process', 'message'):
                log_entry[key] = value
        
        return json.dumps(log_entry)


# Configure specific loggers
def configure_loggers():
    """Configure specific loggers for different components"""
    
    # Silence noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("s3transfer").setLevel(logging.WARNING)
    
    # Configure application loggers
    logging.getLogger("app").setLevel(logging.INFO)
    logging.getLogger("celery").setLevel(logging.INFO)
    
    # Configure security logger
    security_logger = logging.getLogger("security")
    security_logger.setLevel(logging.WARNING)
    
    # Configure audit logger
    audit_logger = logging.getLogger("audit")
    audit_logger.setLevel(logging.INFO)


# Audit logging utilities
def log_security_event(event_type: str, user_id: int = None, details: dict = None):
    """Log security-related events"""
    security_logger = structlog.get_logger("security")
    security_logger.warning(
        "Security event",
        event_type=event_type,
        user_id=user_id,
        details=details or {}
    )


def log_audit_event(action: str, user_id: int, resource_type: str, resource_id: str = None, details: dict = None):
    """Log audit events"""
    audit_logger = structlog.get_logger("audit")
    audit_logger.info(
        "Audit event",
        action=action,
        user_id=user_id,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {}
    )