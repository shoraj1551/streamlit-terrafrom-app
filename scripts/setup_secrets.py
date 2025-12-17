"""
Setup Script for AWS Secrets Manager

This script helps initialize secrets in AWS Secrets Manager for the Terraform-Streamlit application.
Run this once per environment (development, staging, production).

Usage:
    python scripts/setup_secrets.py --environment development
"""

import argparse
import boto3
import json
import os
import sys
from getpass import getpass

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.secrets_manager import SecretsManager
from app.services.encryption import generate_api_key


def setup_app_secrets(secrets_manager: SecretsManager, environment: str):
    """Setup application secrets"""
    print(f"\n📝 Setting up application secrets for {environment}...")
    
    secret_key = input(f"Enter SECRET_KEY (or press Enter to generate): ").strip()
    if not secret_key:
        secret_key = generate_api_key(32)
        print(f"Generated SECRET_KEY: {secret_key}")
    
    encryption_key = input(f"Enter ENCRYPTION_MASTER_KEY (or press Enter to generate): ").strip()
    if not encryption_key:
        encryption_key = generate_api_key(32)
        print(f"Generated ENCRYPTION_MASTER_KEY: {encryption_key}")
    
    debug = input(f"Enable DEBUG mode? (y/N): ").strip().lower() == 'y'
    
    app_secrets = {
        "secret_key": secret_key,
        "encryption_master_key": encryption_key,
        "debug": debug,
        "terraform_state_backend": "local",
    }
    
    secret_name = f"terraform-app/{environment}/app"
    
    try:
        secrets_manager.create_secret(
            name=secret_name,
            secret_value=app_secrets,
            description=f"Application secrets for {environment}",
            tags={"Environment": environment, "Application": "terraform-app"},
        )
        print(f"✅ Created secret: {secret_name}")
    except ValueError as e:
        print(f"⚠️  {e}")
        update = input("Update existing secret? (y/N): ").strip().lower() == 'y'
        if update:
            secrets_manager.update_secret(secret_name, app_secrets)
            print(f"✅ Updated secret: {secret_name}")


def setup_aws_secrets(secrets_manager: SecretsManager, environment: str):
    """Setup AWS credentials"""
    print(f"\n📝 Setting up AWS credentials for {environment}...")
    
    use_iam_role = input("Use IAM role instead of access keys? (Y/n): ").strip().lower() != 'n'
    
    if use_iam_role:
        print("ℹ️  Using IAM role - no credentials needed")
        return
    
    access_key_id = input("Enter AWS_ACCESS_KEY_ID: ").strip()
    secret_access_key = getpass("Enter AWS_SECRET_ACCESS_KEY: ").strip()
    region = input("Enter AWS_REGION (default: us-east-1): ").strip() or "us-east-1"
    
    aws_secrets = {
        "access_key_id": access_key_id,
        "secret_access_key": secret_access_key,
        "region": region,
    }
    
    secret_name = f"terraform-app/{environment}/aws"
    
    try:
        secrets_manager.create_secret(
            name=secret_name,
            secret_value=aws_secrets,
            description=f"AWS credentials for {environment}",
            tags={"Environment": environment, "Application": "terraform-app"},
        )
        print(f"✅ Created secret: {secret_name}")
    except ValueError as e:
        print(f"⚠️  {e}")
        update = input("Update existing secret? (y/N): ").strip().lower() == 'y'
        if update:
            secrets_manager.update_secret(secret_name, aws_secrets)
            print(f"✅ Updated secret: {secret_name}")


def setup_auth_secrets(secrets_manager: SecretsManager, environment: str):
    """Setup authentication provider secrets"""
    print(f"\n📝 Setting up authentication secrets for {environment}...")
    
    provider = input("Auth provider (auth0/cognito): ").strip().lower()
    
    if provider == "auth0":
        domain = input("Enter AUTH0_DOMAIN: ").strip()
        client_id = input("Enter AUTH0_CLIENT_ID: ").strip()
        client_secret = getpass("Enter AUTH0_CLIENT_SECRET: ").strip()
        
        auth_secrets = {
            "domain": domain,
            "client_id": client_id,
            "client_secret": client_secret,
        }
    elif provider == "cognito":
        user_pool_id = input("Enter COGNITO_USER_POOL_ID: ").strip()
        client_id = input("Enter COGNITO_CLIENT_ID: ").strip()
        client_secret = getpass("Enter COGNITO_CLIENT_SECRET (optional): ").strip()
        region = input("Enter COGNITO_REGION (default: us-east-1): ").strip() or "us-east-1"
        
        auth_secrets = {
            "user_pool_id": user_pool_id,
            "client_id": client_id,
            "client_secret": client_secret,
            "region": region,
        }
    else:
        print(f"❌ Unsupported provider: {provider}")
        return
    
    secret_name = f"terraform-app/{environment}/auth-{provider}"
    
    try:
        secrets_manager.create_secret(
            name=secret_name,
            secret_value=auth_secrets,
            description=f"{provider.upper()} authentication secrets for {environment}",
            tags={"Environment": environment, "Application": "terraform-app"},
        )
        print(f"✅ Created secret: {secret_name}")
    except ValueError as e:
        print(f"⚠️  {e}")
        update = input("Update existing secret? (y/N): ").strip().lower() == 'y'
        if update:
            secrets_manager.update_secret(secret_name, auth_secrets)
            print(f"✅ Updated secret: {secret_name}")


def setup_database_secrets(secrets_manager: SecretsManager, environment: str):
    """Setup database credentials"""
    print(f"\n📝 Setting up database secrets for {environment}...")
    
    use_db = input("Configure database? (y/N): ").strip().lower() == 'y'
    
    if not use_db:
        print("ℹ️  Skipping database configuration")
        return
    
    host = input("Enter DB_HOST: ").strip()
    port = input("Enter DB_PORT (default: 5432): ").strip() or "5432"
    database = input("Enter DB_NAME: ").strip()
    username = input("Enter DB_USER: ").strip()
    password = getpass("Enter DB_PASSWORD: ").strip()
    
    db_secrets = {
        "host": host,
        "port": port,
        "database": database,
        "username": username,
        "password": password,
    }
    
    secret_name = f"terraform-app/{environment}/database"
    
    try:
        secrets_manager.create_secret(
            name=secret_name,
            secret_value=db_secrets,
            description=f"Database credentials for {environment}",
            tags={"Environment": environment, "Application": "terraform-app"},
        )
        print(f"✅ Created secret: {secret_name}")
    except ValueError as e:
        print(f"⚠️  {e}")
        update = input("Update existing secret? (y/N): ").strip().lower() == 'y'
        if update:
            secrets_manager.update_secret(secret_name, db_secrets)
            print(f"✅ Updated secret: {secret_name}")


def main():
    parser = argparse.ArgumentParser(description="Setup AWS Secrets Manager for Terraform-Streamlit app")
    parser.add_argument(
        "--environment",
        "-e",
        required=True,
        choices=["development", "staging", "production"],
        help="Environment to setup",
    )
    parser.add_argument(
        "--region",
        "-r",
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )
    
    args = parser.parse_args()
    
    print(f"🚀 Setting up AWS Secrets Manager for environment: {args.environment}")
    print(f"📍 Region: {args.region}")
    print()
    
    # Initialize Secrets Manager
    try:
        secrets_manager = SecretsManager(region=args.region)
    except Exception as e:
        print(f"❌ Failed to initialize Secrets Manager: {e}")
        print("Make sure you have AWS credentials configured")
        sys.exit(1)
    
    # Setup secrets
    try:
        setup_app_secrets(secrets_manager, args.environment)
        setup_aws_secrets(secrets_manager, args.environment)
        setup_auth_secrets(secrets_manager, args.environment)
        setup_database_secrets(secrets_manager, args.environment)
        
        print("\n✅ All secrets configured successfully!")
        print(f"\nTo use these secrets, set environment variable:")
        print(f"  ENVIRONMENT={args.environment}")
        print(f"  USE_SECRETS_MANAGER=true")
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
