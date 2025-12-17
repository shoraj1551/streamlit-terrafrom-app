import pytest
import asyncio
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.terraform_generator import TerraformGenerator
from app.config_parser import InfrastructureConfig


@pytest.fixture
def aws_config():
    return InfrastructureConfig(
        provider="aws",
        region="us-east-1",
        instance_type="t2.micro",
        tags={"Environment": "test", "Project": "pytest"}
    )


@pytest.fixture
def aws_config_with_ami():
    return InfrastructureConfig(
        provider="aws",
        region="us-west-2",
        instance_type="t3.small",
        ami_id="ami-12345678",
        tags={"Environment": "prod"}
    )


def test_generate_aws_config_basic(aws_config):
    """Test generating basic AWS Terraform configuration"""
    result = TerraformGenerator.generate_aws_config(aws_config)
    
    assert "terraform {" in result
    assert "provider \"aws\"" in result
    assert "region = \"us-east-1\"" in result
    assert "resource \"aws_instance\" \"main\"" in result
    assert "instance_type = \"t2.micro\"" in result
    assert "Environment = \"test\"" in result
    assert "Project = \"pytest\"" in result


def test_generate_aws_config_with_ami(aws_config_with_ami):
    """Test generating AWS config with custom AMI"""
    result = TerraformGenerator.generate_aws_config(aws_config_with_ami)
    
    assert "ami-12345678" in result
    assert "data \"aws_ami\"" not in result  # Should not have data source
    assert "region = \"us-west-2\"" in result
    assert "instance_type = \"t3.small\"" in result


def test_generate_aws_config_without_ami(aws_config):
    """Test generating AWS config with dynamic AMI lookup"""
    result = TerraformGenerator.generate_aws_config(aws_config)
    
    assert "data \"aws_ami\" \"selected\"" in result
    assert "amzn2-ami-hvm" in result
    assert "data.aws_ami.selected.id" in result


def test_generate_aws_config_outputs(aws_config):
    """Test that outputs are included"""
    result = TerraformGenerator.generate_aws_config(aws_config)
    
    assert "output \"instance_id\"" in result
    assert "output \"instance_public_ip\"" in result
    assert "output \"instance_private_ip\"" in result
    assert "output \"instance_state\"" in result


def test_preview_config_aws(aws_config):
    """Test preview_config for AWS"""
    result = TerraformGenerator.preview_config(aws_config)
    
    assert isinstance(result, str)
    assert len(result) > 0
    assert "provider \"aws\"" in result


def test_preview_config_azure():
    """Test preview_config for Azure (not implemented)"""
    azure_config = InfrastructureConfig(
        provider="azure",
        region="eastus",
        instance_type="Standard_B1s"
    )
    
    with pytest.raises(NotImplementedError, match="Azure provider not yet implemented"):
        TerraformGenerator.preview_config(azure_config)


def test_preview_config_gcp():
    """Test preview_config for GCP (not implemented)"""
    gcp_config = InfrastructureConfig(
        provider="gcp",
        region="us-central1",
        instance_type="n1-standard-1"
    )
    
    with pytest.raises(NotImplementedError, match="GCP provider not yet implemented"):
        TerraformGenerator.preview_config(gcp_config)


def test_write_config_to_file(aws_config, tmp_path):
    """Test writing Terraform config to file"""
    output_dir = tmp_path / "terraform"
    
    result_path = TerraformGenerator.write_config_to_file(aws_config, output_dir)
    
    assert result_path.exists()
    assert result_path.name == "main.tf"
    assert result_path.parent == output_dir
    
    # Read and verify content
    content = result_path.read_text()
    assert "provider \"aws\"" in content
    assert "resource \"aws_instance\" \"main\"" in content


def test_write_config_creates_directory(aws_config, tmp_path):
    """Test that write_config_to_file creates directory if it doesn't exist"""
    output_dir = tmp_path / "new" / "nested" / "dir"
    
    assert not output_dir.exists()
    
    result_path = TerraformGenerator.write_config_to_file(aws_config, output_dir)
    
    assert output_dir.exists()
    assert result_path.exists()


def test_generate_config_no_tags():
    """Test generating config without tags"""
    config = InfrastructureConfig(
        provider="aws",
        region="us-east-1",
        instance_type="t2.micro"
    )
    
    result = TerraformGenerator.generate_aws_config(config)
    
    assert "ManagedBy = \"Streamlit-Terraform\"" in result


def test_terraform_config_syntax(aws_config):
    """Test that generated config has valid HCL syntax"""
    result = TerraformGenerator.generate_aws_config(aws_config)
    
    # Check for balanced braces
    assert result.count("{") == result.count("}")
    
    # Check for required blocks
    assert "terraform {" in result
    assert "provider \"aws\" {" in result
    assert "resource \"aws_instance\" \"main\" {" in result
    
    # Check for proper closing
    assert result.strip().endswith("}")
