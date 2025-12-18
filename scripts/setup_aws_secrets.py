"""
AWS Secrets Manager Setup Script

Creates required secrets in AWS Secrets Manager for the application.
Run this script once during initial setup.
"""

import boto3
import json
import sys
from botocore.exceptions import ClientError

# Import key generation from encryption module
sys.path.insert(0, '..')
from app.services.encryption import generate_api_key


def create_secret(client, name, secret_data, description):
    """Create or update a secret in AWS Secrets Manager"""
    try:
        # Try to create the secret
        response = client.create_secret(
            Name=name,
            SecretString=json.dumps(secret_data),
            Description=description
        )
        print(f"✅ Created secret: {name}")
        return response['ARN']
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceExistsException':
            # Secret already exists, update it
            response = client.update_secret(
                SecretId=name,
                SecretString=json.dumps(secret_data)
            )
            print(f"✅ Updated existing secret: {name}")
            return response['ARN']
        else:
            print(f"❌ Error creating secret {name}: {e}")
            raise


def setup_secrets(region='us-east-1'):
    """
    Setup all required secrets in AWS Secrets Manager
    
    Args:
        region: AWS region for Secrets Manager
    """
    print("=" * 60)
    print("AWS Secrets Manager Setup")
    print("=" * 60)
    print()
    
    # Initialize Secrets Manager client
    try:
        client = boto3.client('secretsmanager', region_name=region)
        print(f"✅ Connected to AWS Secrets Manager in {region}")
    except Exception as e:
        print(f"❌ Failed to connect to AWS: {e}")
        print("\nMake sure you have:")
        print("1. AWS credentials configured (aws configure)")
        print("2. Proper IAM permissions for Secrets Manager")
        return
    
    print()
    
    # 1. Application Secret Key
    print("Creating application secret key...")
    secret_key = generate_api_key(32)
    create_secret(
        client,
        'terraform-app/secret-key',
        {'secret_key': secret_key},
        'Application secret key for JWT signing and session management'
    )
    
    # 2. Encryption Master Key
    print("\nCreating encryption master key...")
    encryption_key = generate_api_key(32)
    create_secret(
        client,
        'terraform-app/encryption-key',
        {'master_key': encryption_key},
        'Master encryption key for data at rest encryption'
    )
    
    # 3. Database Credentials
    print("\nCreating database credentials...")
    db_password = generate_api_key(32)
    db_host = input("Enter PostgreSQL host (e.g., your-rds-endpoint.amazonaws.com): ").strip()
    if not db_host:
        db_host = "localhost"
    
    create_secret(
        client,
        'terraform-app/database',
        {
            'username': 'terraform_user',
            'password': db_password,
            'host': db_host,
            'port': 5432,
            'database': 'terraform_app'
        },
        'PostgreSQL database credentials'
    )
    
    # 4. Redis Credentials
    print("\nCreating Redis credentials...")
    redis_password = generate_api_key(32)
    redis_host = input("Enter Redis host (default: localhost): ").strip()
    if not redis_host:
        redis_host = "localhost"
    
    create_secret(
        client,
        'terraform-app/redis',
        {
            'host': redis_host,
            'port': 6379,
            'password': redis_password,
            'db': 0
        },
        'Redis cache credentials'
    )
    
    print()
    print("=" * 60)
    print("✅ All secrets created successfully!")
    print("=" * 60)
    print()
    print("📝 IMPORTANT NOTES:")
    print()
    print("1. Update your .env file with:")
    print(f"   AWS_REGION={region}")
    print("   USE_AWS_SECRETS=true")
    print()
    print("2. Ensure your application has IAM permissions:")
    print("   - secretsmanager:GetSecretValue")
    print("   - secretsmanager:DescribeSecret")
    print()
    print("3. For production, use different secrets for each environment")
    print()
    print("4. Enable automatic rotation for database credentials:")
    print("   https://docs.aws.amazon.com/secretsmanager/latest/userguide/rotating-secrets.html")
    print()
    print("=" * 60)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Setup AWS Secrets Manager')
    parser.add_argument(
        '--region',
        default='us-east-1',
        help='AWS region (default: us-east-1)'
    )
    
    args = parser.parse_args()
    
    setup_secrets(args.region)
