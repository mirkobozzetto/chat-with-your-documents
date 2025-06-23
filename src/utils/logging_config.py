# src/utils/logging_config.py
import logging
import logging.handlers
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class SecurityAwareFormatter(logging.Formatter):
    """Custom formatter that sanitizes sensitive information from logs"""
    
    SENSITIVE_KEYS = {
        'password', 'token', 'key', 'secret', 'api_key', 'auth', 'credential',
        'jwt', 'session', 'cookie', 'openai_api_key', 'jwt_secret_key'
    }
    
    def format(self, record):
        original_msg = record.getMessage()
        
        if hasattr(record, 'extra_data') and record.extra_data:
            sanitized_data = self._sanitize_dict(record.extra_data)
            record.extra_data = sanitized_data
        
        sanitized_msg = self._sanitize_message(original_msg)
        record.msg = sanitized_msg
        record.args = ()
        
        formatted = super().format(record)
        
        return formatted
    
    def _sanitize_message(self, message: str) -> str:
        """Sanitize sensitive information from log messages"""
        if not isinstance(message, str):
            return str(message)
        
        for sensitive_key in self.SENSITIVE_KEYS:
            if sensitive_key in message.lower():
                import re
                pattern = rf'({sensitive_key}["\'\s]*[:=]["\'\s]*)([^"\'\s,}}\]]+)'
                message = re.sub(pattern, r'\1***REDACTED***', message, flags=re.IGNORECASE)
        
        return message
    
    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary data"""
        if not isinstance(data, dict):
            return data
        
        sanitized = {}
        for key, value in data.items():
            if isinstance(key, str) and any(sensitive in key.lower() for sensitive in self.SENSITIVE_KEYS):
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, list):
                sanitized[key] = [self._sanitize_dict(item) if isinstance(item, dict) else item for item in value]
            else:
                sanitized[key] = value
        
        return sanitized


class StructuredLogger:
    """Structured logging with security features and context management"""
    
    def __init__(self, name: str, log_level: str = "INFO"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        if not self.logger.handlers:
            self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup console and file handlers with appropriate formatters"""
        
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        file_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)
        
        security_handler = logging.handlers.RotatingFileHandler(
            logs_dir / "security.log",
            maxBytes=5*1024*1024,   # 5MB
            backupCount=10
        )
        security_handler.setLevel(logging.WARNING)
        
        console_format = SecurityAwareFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        file_format = SecurityAwareFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
        )
        
        console_handler.setFormatter(console_format)
        file_handler.setFormatter(file_format)
        security_handler.setFormatter(file_format)
        
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        
        security_logger = logging.getLogger(f"{self.logger.name}.security")
        security_logger.addHandler(security_handler)
        security_logger.propagate = False
    
    def _log_structured(self, level: int, message: str, **kwargs):
        """Log with structured data"""
        extra_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'component': self.logger.name,
            **kwargs
        }
        
        record = self.logger.makeRecord(
            self.logger.name, level, "", 0, message, (), None,
            extra={'extra_data': extra_data}
        )
        
        self.logger.handle(record)
    
    def info(self, message: str, **kwargs):
        """Log info level message with structured data"""
        self._log_structured(logging.INFO, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug level message with structured data"""
        self._log_structured(logging.DEBUG, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning level message with structured data"""
        self._log_structured(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log error level message with optional exception details"""
        if error:
            kwargs.update({
                'error_type': type(error).__name__,
                'error_message': str(error),
                'error_traceback': self._get_traceback_string(error)
            })
        
        self._log_structured(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, error: Optional[Exception] = None, **kwargs):
        """Log critical level message with optional exception details"""
        if error:
            kwargs.update({
                'error_type': type(error).__name__,
                'error_message': str(error),
                'error_traceback': self._get_traceback_string(error)
            })
        
        self._log_structured(logging.CRITICAL, message, **kwargs)
    
    def security_event(self, event_type: str, message: str, **kwargs):
        """Log security-related events"""
        security_logger = logging.getLogger(f"{self.logger.name}.security")
        
        security_data = {
            'security_event': True,
            'event_type': event_type,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
        
        record = security_logger.makeRecord(
            security_logger.name, logging.WARNING, "", 0, message, (), None,
            extra={'extra_data': security_data}
        )
        
        security_logger.handle(record)
    
    def audit_trail(self, action: str, user_id: str, resource: str, **kwargs):
        """Log audit trail for important user actions"""
        audit_data = {
            'audit': True,
            'action': action,
            'user_id': user_id,
            'resource': resource,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
        
        self._log_structured(logging.INFO, f"AUDIT: {action} on {resource} by {user_id}", **audit_data)
    
    def performance_metric(self, operation: str, duration: float, **kwargs):
        """Log performance metrics"""
        perf_data = {
            'performance': True,
            'operation': operation,
            'duration_seconds': duration,
            'timestamp': datetime.utcnow().isoformat(),
            **kwargs
        }
        
        self._log_structured(logging.INFO, f"PERF: {operation} took {duration:.3f}s", **perf_data)
    
    def _get_traceback_string(self, error: Exception) -> str:
        """Get formatted traceback string from exception"""
        import traceback
        return ''.join(traceback.format_exception(type(error), error, error.__traceback__))


def get_logger(name: str, log_level: str = None) -> StructuredLogger:
    """Get a configured structured logger instance"""
    if log_level is None:
        log_level = os.getenv("LOG_LEVEL", "INFO")
    
    return StructuredLogger(name, log_level)


def setup_global_logging():
    """Setup global logging configuration"""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[]
    )
    
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


class LoggerMixin:
    """Mixin class to add logging capabilities to any class"""
    
    @property
    def logger(self) -> StructuredLogger:
        if not hasattr(self, '_logger'):
            class_name = self.__class__.__module__ + '.' + self.__class__.__name__
            self._logger = get_logger(class_name)
        return self._logger