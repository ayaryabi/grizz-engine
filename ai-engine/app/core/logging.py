import logging
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
import traceback
from contextvars import ContextVar

# Request context variable for tracing
request_id_var: ContextVar[Optional[str]] = ContextVar('request_id', default=None)

class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'request_id': request_id_var.get(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'user_id'):
            log_entry['user_id'] = record.user_id
        if hasattr(record, 'conversation_id'):
            log_entry['conversation_id'] = record.conversation_id
        if hasattr(record, 'duration_ms'):
            log_entry['duration_ms'] = record.duration_ms
        if hasattr(record, 'error_type'):
            log_entry['error_type'] = record.error_type
        if hasattr(record, 'db_pool_info'):
            log_entry['db_pool_info'] = record.db_pool_info
            
        # Add exception info if present
        if record.exc_info:
            log_entry['exception'] = {
                'type': record.exc_info[0].__name__,
                'message': str(record.exc_info[1]),
                'traceback': traceback.format_exception(*record.exc_info)
            }
            
        return json.dumps(log_entry)

def setup_logging():
    """Setup structured logging for the application"""
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create console handler with structured formatter
    handler = logging.StreamHandler()
    handler.setFormatter(StructuredFormatter())
    logger.addHandler(handler)
    
    return logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the given name"""
    return logging.getLogger(name)

def set_request_id(request_id: str = None) -> str:
    """Set the request ID for the current context"""
    if request_id is None:
        request_id = str(uuid.uuid4())[:8]
    request_id_var.set(request_id)
    return request_id

def get_request_id() -> Optional[str]:
    """Get the current request ID"""
    return request_id_var.get()

def log_db_operation(logger: logging.Logger, operation: str, duration_ms: float, success: bool, error: str = None):
    """Log database operations with timing and success/failure"""
    extra = {
        'duration_ms': duration_ms,
        'operation': operation,
        'success': success
    }
    if error:
        extra['error_type'] = type(error).__name__ if hasattr(error, '__class__') else 'Unknown'
        
    if success:
        logger.info(f"DB operation '{operation}' completed successfully", extra=extra)
    else:
        logger.error(f"DB operation '{operation}' failed: {error}", extra=extra)

def log_redis_operation(logger: logging.Logger, operation: str, duration_ms: float, success: bool, error: str = None):
    """Log Redis operations with timing and success/failure"""
    extra = {
        'duration_ms': duration_ms,
        'operation': operation,
        'success': success
    }
    if error:
        extra['error_type'] = type(error).__name__ if hasattr(error, '__class__') else 'Unknown'
        
    if success:
        logger.info(f"Redis operation '{operation}' completed successfully", extra=extra)
    else:
        logger.error(f"Redis operation '{operation}' failed: {error}", extra=extra)

def log_api_request(logger: logging.Logger, method: str, path: str, status_code: int, duration_ms: float, user_id: str = None):
    """Log API requests with timing and user context"""
    extra = {
        'duration_ms': duration_ms,
        'method': method,
        'path': path,
        'status_code': status_code
    }
    if user_id:
        extra['user_id'] = user_id
        
    logger.info(f"{method} {path} -> {status_code}", extra=extra) 