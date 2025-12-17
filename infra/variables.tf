variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t2.micro"
  
  validation {
    condition     = can(regex("^t[234]\\.", var.instance_type)) || can(regex("^[mc]5\\.", var.instance_type))
    error_message = "Instance type must be a valid AWS instance type (t2.*, t3.*, t4g.*, m5.*, c5.*)."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
  
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "project_name" {
  description = "Project name for resource tagging"
  type        = string
  default     = "streamlit-terraform"
}

variable "ami_id" {
  description = "AMI ID for the instance (optional, will use latest Amazon Linux 2 if not specified)"
  type        = string
  default     = null
}
