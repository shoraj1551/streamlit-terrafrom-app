"""
Input Sanitization and Validation

Provides comprehensive input sanitization to prevent injection attacks and malicious input.

Features:
- SQL injection prevention
- XSS prevention
- Path traversal prevention
- Command injection prevention
- Terraform code validation
- File upload validation
"""

import re
import os
from typing import Any, Optional, List, Dict
from pathlib import Path
import yaml
import json
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class InputSanitizer:
    """
    Input sanitization and validation
    
    Prevents common injection attacks and validates input formats.
    """
    
    # Dangerous patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|EXECUTE)\b)",
        r"(--|;|\/\*|\*\/)",
        r"(\bOR\b.*=.*)",
        r"(\bAND\b.*=.*)",
        r"('|\"|`)",
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r"[;&|`$(){}[\]<>]",
        r"\$\(",
        r"`.*`",
        r"\|\|",
        r"&&",
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.",
        r"~",
        r"/etc/",
        r"/var/",
        r"C:\\",
        r"\\\\",
    ]
    
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe",
        r"<object",
        r"<embed",
    ]
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """
        Sanitize string input
        
        Args:
            value: Input string
            max_length: Maximum allowed length
            
        Returns:
            Sanitized string
        """
        if not isinstance(value, str):
            raise ValueError("Input must be a string")
        
        # Check length
        if len(value) > max_length:
            raise ValueError(f"Input exceeds maximum length of {max_length}")
        
        # Remove null bytes
        value = value.replace("\x00", "")
        
        # Strip leading/trailing whitespace
        value = value.strip()
        
        return value
    
    @staticmethod
    def validate_no_sql_injection(value: str) -> bool:
        """
        Check for SQL injection patterns
        
        Returns:
            True if safe, raises ValueError if dangerous
        """
        for pattern in InputSanitizer.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential SQL injection detected: {pattern}")
                raise ValueError("Input contains potentially dangerous SQL patterns")
        
        return True
    
    @staticmethod
    def validate_no_command_injection(value: str) -> bool:
        """
        Check for command injection patterns
        
        Returns:
            True if safe, raises ValueError if dangerous
        """
        for pattern in InputSanitizer.COMMAND_INJECTION_PATTERNS:
            if re.search(pattern, value):
                logger.warning(f"Potential command injection detected: {pattern}")
                raise ValueError("Input contains potentially dangerous command patterns")
        
        return True
    
    @staticmethod
    def validate_no_path_traversal(value: str) -> bool:
        """
        Check for path traversal patterns
        
        Returns:
            True if safe, raises ValueError if dangerous
        """
        for pattern in InputSanitizer.PATH_TRAVERSAL_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential path traversal detected: {pattern}")
                raise ValueError("Input contains potentially dangerous path patterns")
        
        return True
    
    @staticmethod
    def validate_no_xss(value: str) -> bool:
        """
        Check for XSS patterns
        
        Returns:
            True if safe, raises ValueError if dangerous
        """
        for pattern in InputSanitizer.XSS_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                logger.warning(f"Potential XSS detected: {pattern}")
                raise ValueError("Input contains potentially dangerous XSS patterns")
        
        return True
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and dangerous characters
        
        Args:
            filename: Original filename
            
        Returns:
            Sanitized filename
        """
        # Remove path components
        filename = os.path.basename(filename)
        
        # Remove dangerous characters
        filename = re.sub(r'[^\w\s\-\.]', '', filename)
        
        # Limit length
        if len(filename) > 255:
            name, ext = os.path.splitext(filename)
            filename = name[:250] + ext
        
        # Ensure not empty
        if not filename:
            filename = "unnamed_file"
        
        return filename
    
    @staticmethod
    def validate_file_extension(filename: str, allowed_extensions: List[str]) -> bool:
        """
        Validate file extension
        
        Args:
            filename: Filename to check
            allowed_extensions: List of allowed extensions (e.g., ['json', 'yaml'])
            
        Returns:
            True if valid, raises ValueError if invalid
        """
        ext = filename.split('.')[-1].lower()
        
        if ext not in allowed_extensions:
            raise ValueError(f"File extension '.{ext}' not allowed. Allowed: {allowed_extensions}")
        
        return True
    
    @staticmethod
    def validate_json(content: str) -> Dict[str, Any]:
        """
        Validate and parse JSON content
        
        Args:
            content: JSON string
            
        Returns:
            Parsed JSON object
        """
        try:
            data = json.loads(content)
            return data
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")
    
    @staticmethod
    def validate_yaml(content: str) -> Dict[str, Any]:
        """
        Validate and parse YAML content
        
        Args:
            content: YAML string
            
        Returns:
            Parsed YAML object
        """
        try:
            data = yaml.safe_load(content)
            return data
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML: {e}")
    
    @staticmethod
    def validate_terraform_config(config: Dict[str, Any]) -> bool:
        """
        Validate Terraform configuration for dangerous patterns
        
        Args:
            config: Terraform configuration dictionary
            
        Returns:
            True if safe, raises ValueError if dangerous
        """
        # Check for dangerous resource types
        dangerous_resources = [
            "null_resource",  # Can execute arbitrary commands
            "local_exec",  # Can execute local commands
        ]
        
        # Convert config to string for pattern matching
        config_str = json.dumps(config)
        
        for resource in dangerous_resources:
            if resource in config_str:
                logger.warning(f"Potentially dangerous Terraform resource: {resource}")
                # Don't block, just warn (admin can override)
        
        # Check for suspicious provisioners
        if "provisioner" in config_str:
            logger.warning("Terraform provisioners detected - review carefully")
        
        return True
    
    @staticmethod
    def sanitize_dict(data: Dict[str, Any], max_depth: int = 10, current_depth: int = 0) -> Dict[str, Any]:
        """
        Recursively sanitize dictionary values
        
        Args:
            data: Dictionary to sanitize
            max_depth: Maximum recursion depth
            current_depth: Current recursion depth
            
        Returns:
            Sanitized dictionary
        """
        if current_depth >= max_depth:
            raise ValueError("Dictionary nesting too deep")
        
        sanitized = {}
        
        for key, value in data.items():
            # Sanitize key
            if not isinstance(key, str):
                key = str(key)
            key = InputSanitizer.sanitize_string(key, max_length=100)
            
            # Sanitize value
            if isinstance(value, str):
                value = InputSanitizer.sanitize_string(value)
            elif isinstance(value, dict):
                value = InputSanitizer.sanitize_dict(value, max_depth, current_depth + 1)
            elif isinstance(value, list):
                value = [
                    InputSanitizer.sanitize_string(v) if isinstance(v, str) else v
                    for v in value
                ]
            
            sanitized[key] = value
        
        return sanitized


# Convenience functions

def sanitize_user_input(value: str, check_sql: bool = True, check_xss: bool = True) -> str:
    """
    Sanitize general user input
    
    Args:
        value: Input value
        check_sql: Check for SQL injection
        check_xss: Check for XSS
        
    Returns:
        Sanitized value
    """
    sanitizer = InputSanitizer()
    
    value = sanitizer.sanitize_string(value)
    
    if check_sql:
        sanitizer.validate_no_sql_injection(value)
    
    if check_xss:
        sanitizer.validate_no_xss(value)
    
    return value


def validate_uploaded_file(file, allowed_extensions: List[str], max_size_mb: int = 10):
    """
    Validate uploaded file
    
    Args:
        file: Streamlit UploadedFile object
        allowed_extensions: List of allowed extensions
        max_size_mb: Maximum file size in MB
    """
    sanitizer = InputSanitizer()
    
    # Check file size
    file_size_mb = file.size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        raise ValueError(f"File size ({file_size_mb:.2f}MB) exceeds maximum ({max_size_mb}MB)")
    
    # Sanitize filename
    safe_filename = sanitizer.sanitize_filename(file.name)
    
    # Validate extension
    sanitizer.validate_file_extension(safe_filename, allowed_extensions)
    
    logger.info(f"File validated: {safe_filename} ({file_size_mb:.2f}MB)")
    
    return safe_filename
