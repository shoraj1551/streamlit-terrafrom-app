"""
Structured Logging System

Provides comprehensive logging with JSON format, multiple outputs, and filtering.
"""

import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path


class StructuredLogger:
    """Structured logging with JSON format"""
    
    def __init__(self, name: str, log_dir: Path = None):
        self.logger = logging.getLogger(name)
        self.log_dir = log_dir or Path("./logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Prevent duplicate handlers
        if not self.logger.handlers:
            self._setup_handlers()
        
        self.logger.setLevel(logging.INFO)
    
    def _setup_handlers(self):
        """Setup file and console handlers"""
        # File handler for JSON logs
        log_file = self.log_dir / f"{datetime.now().strftime('%Y%m%d')}.jsonl"
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(self.JSONFormatter())
        self.logger.addHandler(file_handler)
        
        # Console handler for human-readable logs
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.HumanFormatter())
        self.logger.addHandler(console_handler)
    
    class JSONFormatter(logging.Formatter):
        """Format logs as JSON Lines"""
        def format(self, record):
            log_data = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'level': record.levelname,
                'logger': record.name,
                'message': record.getMessage(),
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
            }
            
            # Add extra fields
            for key in ['deployment_id', 'user_id', 'cloud_provider', 'environment', 'action']:
                if hasattr(record, key):
                    log_data[key] = getattr(record, key)
            
            # Add exception info if present
            if record.exc_info:
                log_data['exception'] = self.formatException(record.exc_info)
            
            return json.dumps(log_data)
    
    class HumanFormatter(logging.Formatter):
        """Format logs for human reading"""
        def format(self, record):
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            level_colors = {
                'DEBUG': '\033[36m',    # Cyan
                'INFO': '\033[32m',     # Green
                'WARNING': '\033[33m',  # Yellow
                'ERROR': '\033[31m',    # Red
                'CRITICAL': '\033[35m', # Magenta
            }
            reset = '\033[0m'
            
            color = level_colors.get(record.levelname, '')
            level = f"{color}{record.levelname:8}{reset}"
            
            msg = f"{timestamp} | {level} | {record.name} | {record.getMessage()}"
            
            # Add deployment ID if present
            if hasattr(record, 'deployment_id'):
                msg += f" | deployment={record.deployment_id[:8]}"
            
            return msg
    
    def log_deployment(
        self, 
        level: str, 
        message: str, 
        deployment_id: str,
        cloud_provider: Optional[str] = None,
        environment: Optional[str] = None,
        **kwargs
    ):
        """Log deployment-related event"""
        extra = {
            'deployment_id': deployment_id,
            'action': 'deployment',
            **kwargs
        }
        
        if cloud_provider:
            extra['cloud_provider'] = cloud_provider
        if environment:
            extra['environment'] = environment
        
        getattr(self.logger, level.lower())(message, extra=extra)
    
    def log_user_action(
        self,
        level: str,
        message: str,
        user_id: str,
        action: str,
        **kwargs
    ):
        """Log user action"""
        extra = {
            'user_id': user_id,
            'action': action,
            **kwargs
        }
        
        getattr(self.logger, level.lower())(message, extra=extra)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(message, extra=kwargs)
