#!/usr/bin/env python3
"""
AWS CDK Application Entry Point

This is the main entry point for the CDK application.
It defines the app and instantiates the infrastructure stack.
"""
import os
import aws_cdk as cdk
from stacks.base_stack import BaseStack


app = cdk.App()

# Get environment name from context or environment variable
env_name = app.node.try_get_context("environment") or os.environ.get("ENVIRONMENT", "dev")

# Get environment-specific configuration from cdk.json
env_config = app.node.try_get_context("environments").get(env_name)

if not env_config:
    raise ValueError(
        f"Environment '{env_name}' not found in cdk.json context. "
        f"Valid environments: dev, staging, prod"
    )

# Set up AWS environment
account = env_config.get("account") or os.environ.get('CDK_DEFAULT_ACCOUNT')
region = env_config.get("region") or os.environ.get('CDK_DEFAULT_REGION', 'us-east-1')

env = cdk.Environment(account=account, region=region)

# Instantiate the base stack with environment-specific config
BaseStack(
    app,
    f"AwsBedrockRag-{env_name}",
    env=env,
    env_name=env_name,
    env_config=env_config,
    description=f"AWS Bedrock RAG API Infrastructure Stack ({env_name})"
)

app.synth()
