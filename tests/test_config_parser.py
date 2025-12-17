import pytest
import json
import yaml
from pathlib import Path
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.config_parser import ConfigParser, InfrastructureConfig


@pytest.fixture
def valid_config_dict():
    return {
        "provider": "aws",
        "region": "us-east-1",
        "instance_type": "t2.micro",
        "ami_id": "ami-12345678",
        "tags": {"Environment": "test", "Project": "demo"}
    }


@pytest.fixture
def valid_json_file(tmp_path, valid_config_dict):
    file_path = tmp_path / "config.json"
    with open(file_path, "w") as f:
        json.dump(valid_config_dict, f)
    return file_path


@pytest.fixture
def valid_yaml_file(tmp_path, valid_config_dict):
    file_path = tmp_path / "config.yaml"
    with open(file_path, "w") as f:
        yaml.dump(valid_config_dict, f)
    return file_path


def test_parse_valid_json_file(valid_json_file):
    """Test parsing a valid JSON configuration file"""
    config = ConfigParser.parse_file(valid_json_file)
    
    assert isinstance(config, InfrastructureConfig)
    assert config.provider == "aws"
    assert config.region == "us-east-1"
    assert config.instance_type == "t2.micro"
    assert config.ami_id == "ami-12345678"
    assert config.tags["Environment"] == "test"


def test_parse_valid_yaml_file(valid_yaml_file):
    """Test parsing a valid YAML configuration file"""
    config = ConfigParser.parse_file(valid_yaml_file)
    
    assert isinstance(config, InfrastructureConfig)
    assert config.provider == "aws"
    assert config.region == "us-east-1"
    assert config.instance_type == "t2.micro"


def test_parse_nonexistent_file():
    """Test parsing a file that doesn't exist"""
    with pytest.raises(FileNotFoundError):
        ConfigParser.parse_file("nonexistent.json")


def test_parse_invalid_provider(tmp_path):
    """Test parsing with invalid provider"""
    invalid_config = {
        "provider": "invalid_provider",
        "region": "us-east-1",
        "instance_type": "t2.micro"
    }
    
    file_path = tmp_path / "invalid.json"
    with open(file_path, "w") as f:
        json.dump(invalid_config, f)
    
    with pytest.raises(ValueError, match="Provider must be one of"):
        ConfigParser.parse_file(file_path)


def test_parse_missing_required_field(tmp_path):
    """Test parsing with missing required field"""
    incomplete_config = {
        "provider": "aws",
        "region": "us-east-1"
        # Missing instance_type
    }
    
    file_path = tmp_path / "incomplete.json"
    with open(file_path, "w") as f:
        json.dump(incomplete_config, f)
    
    with pytest.raises(ValueError, match="validation failed"):
        ConfigParser.parse_file(file_path)


def test_parse_invalid_json(tmp_path):
    """Test parsing invalid JSON"""
    file_path = tmp_path / "invalid.json"
    with open(file_path, "w") as f:
        f.write("{invalid json}")
    
    with pytest.raises(ValueError, match="Invalid JSON format"):
        ConfigParser.parse_file(file_path)


def test_parse_invalid_yaml(tmp_path):
    """Test parsing invalid YAML"""
    file_path = tmp_path / "invalid.yaml"
    with open(file_path, "w") as f:
        f.write("invalid: yaml: content: [")
    
    with pytest.raises(ValueError, match="Invalid YAML format"):
        ConfigParser.parse_file(file_path)


def test_file_size_limit(tmp_path):
    """Test file size validation"""
    large_file = tmp_path / "large.json"
    
    # Create a file larger than MAX_FILE_SIZE_MB (10MB)
    with open(large_file, "w") as f:
        # Write 11MB of data
        f.write("x" * (11 * 1024 * 1024))
    
    with pytest.raises(ValueError, match="exceeds maximum allowed size"):
        ConfigParser.parse_file(large_file)


def test_unsupported_file_format(tmp_path):
    """Test unsupported file format"""
    file_path = tmp_path / "config.txt"
    file_path.write_text("some content")
    
    with pytest.raises(ValueError, match="Unsupported file format"):
        ConfigParser.parse_file(file_path)


def test_provider_case_insensitive(tmp_path):
    """Test that provider validation is case insensitive"""
    config_dict = {
        "provider": "AWS",  # Uppercase
        "region": "us-east-1",
        "instance_type": "t2.micro"
    }
    
    file_path = tmp_path / "config.json"
    with open(file_path, "w") as f:
        json.dump(config_dict, f)
    
    config = ConfigParser.parse_file(file_path)
    assert config.provider == "aws"  # Should be lowercased


def test_optional_fields(tmp_path):
    """Test that optional fields work correctly"""
    minimal_config = {
        "provider": "aws",
        "region": "us-east-1",
        "instance_type": "t2.micro"
        # No ami_id or tags
    }
    
    file_path = tmp_path / "minimal.json"
    with open(file_path, "w") as f:
        json.dump(minimal_config, f)
    
    config = ConfigParser.parse_file(file_path)
    assert config.ami_id is None
    assert config.tags == {}


def test_all_providers(tmp_path):
    """Test all supported providers"""
    providers = ["aws", "azure", "gcp"]
    
    for provider in providers:
        config_dict = {
            "provider": provider,
            "region": "us-east-1",
            "instance_type": "t2.micro"
        }
        
        file_path = tmp_path / f"{provider}.json"
        with open(file_path, "w") as f:
            json.dump(config_dict, f)
        
        config = ConfigParser.parse_file(file_path)
        assert config.provider == provider


def test_yml_extension(tmp_path, valid_config_dict):
    """Test that .yml extension is supported"""
    file_path = tmp_path / "config.yml"
    with open(file_path, "w") as f:
        yaml.dump(valid_config_dict, f)
    
    config = ConfigParser.parse_file(file_path)
    assert isinstance(config, InfrastructureConfig)
