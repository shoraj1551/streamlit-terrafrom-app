# Configuration Examples

This document provides comprehensive examples of JSON and YAML configuration files for infrastructure deployment.

## JSON Configuration Format

### Basic EC2 Instance

```json
{
  "provider": "aws",
  "region": "us-east-1",
  "instance_type": "t2.micro",
  "ami_id": "ami-0c55b159cbfafe1f0",
  "tags": {
    "Name": "MyWebServer",
    "Environment": "production",
    "ManagedBy": "terraform-streamlit-app"
  }
}
```

### Development Environment

```json
{
  "provider": "aws",
  "region": "us-east-1",
  "instance_type": "t2.micro",
  "tags": {
    "Name": "DevServer",
    "Environment": "development",
    "AutoShutdown": "true",
    "Owner": "DevTeam"
  }
}
```

### Production Environment

```json
{
  "provider": "aws",
  "region": "us-east-1",
  "instance_type": "t3.medium",
  "ami_id": "ami-0c55b159cbfafe1f0",
  "tags": {
    "Name": "ProdWebServer",
    "Environment": "production",
    "HighAvailability": "true",
    "Monitoring": "enabled",
    "Backup": "hourly",
    "CostCenter": "Engineering"
  }
}
```

## YAML Configuration Format

### Basic EC2 Instance

```yaml
provider: aws
region: us-west-2
instance_type: t2.small
ami_id: ami-0c55b159cbfafe1f0

tags:
  Name: ProductionServer
  Environment: production
  ManagedBy: terraform-streamlit-app
```

### Multi-Region Setup

```yaml
provider: aws
region: eu-central-1
instance_type: t3.small
ami_id: ami-0a1ee2fb28fe05df3

tags:
  Name: EUServer
  Environment: production
  Region: Europe
  Compliance: GDPR
  DataResidency: EU
```

### Testing Environment

```yaml
provider: aws
region: us-west-1
instance_type: t2.micro

tags:
  Name: TestServer
  Environment: testing
  AutoDelete: "true"
  Purpose: QA
```

## Configuration Fields

### Required Fields

- **provider** (string): Cloud provider
  - Supported: `aws`, `azure`, `gcp`
  - Example: `"provider": "aws"`

- **region** (string): AWS region
  - Example: `"region": "us-east-1"`
  - See supported regions below

- **instance_type** (string): EC2 instance type
  - Example: `"instance_type": "t2.micro"`
  - See supported instance types below

### Optional Fields

- **ami_id** (string): Amazon Machine Image ID
  - If not specified, uses latest Amazon Linux 2
  - Example: `"ami_id": "ami-0c55b159cbfafe1f0"`

- **tags** (object): Resource tags
  - Key-value pairs for resource organization
  - Example: `{"Environment": "production", "Owner": "DevOps"}`

## Supported Instance Types

### Free Tier Eligible
- **t2.micro** - 1 vCPU, 1 GB RAM (750 hours/month free)

### General Purpose
- **t2.small** - 1 vCPU, 2 GB RAM
- **t2.medium** - 2 vCPU, 4 GB RAM
- **t3.micro** - 2 vCPU, 1 GB RAM
- **t3.small** - 2 vCPU, 2 GB RAM
- **t3.medium** - 2 vCPU, 4 GB RAM

### Compute Optimized
- **c5.large** - 2 vCPU, 4 GB RAM
- **c5.xlarge** - 4 vCPU, 8 GB RAM

### Memory Optimized
- **r5.large** - 2 vCPU, 16 GB RAM
- **r5.xlarge** - 4 vCPU, 32 GB RAM

## Supported AWS Regions

- **us-east-1** - US East (N. Virginia)
- **us-east-2** - US East (Ohio)
- **us-west-1** - US West (N. California)
- **us-west-2** - US West (Oregon)
- **eu-west-1** - Europe (Ireland)
- **eu-central-1** - Europe (Frankfurt)
- **ap-southeast-1** - Asia Pacific (Singapore)
- **ap-northeast-1** - Asia Pacific (Tokyo)

## Best Practices

1. **Always specify tags** for resource organization
2. **Use t2.micro** for testing (free tier eligible)
3. **Specify AMI ID** for production deployments
4. **Include Environment tag** for cost tracking
5. **Add Owner tag** for accountability
