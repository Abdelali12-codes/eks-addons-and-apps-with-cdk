#!/bin/bash
set -e

echo "Bootstrapping CDK environment..."

# Check prerequisites
command -v python3 >/dev/null 2>&1 || { echo "Python 3 is required but not installed."; exit 1; }
command -v node >/dev/null 2>&1 || { echo "Node.js is required but not installed."; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "AWS CLI is required but not installed."; exit 1; }

# Get AWS account and region
ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
REGION=$(aws configure get region)

echo "AWS Account: $ACCOUNT"
echo "AWS Region: $REGION"

# Install CDK if not present
if ! command -v cdk &> /dev/null; then
    echo "Installing AWS CDK..."
    npm install -g aws-cdk
fi

# Bootstrap CDK
echo "Bootstrapping CDK in $REGION..."
cdk bootstrap aws://$ACCOUNT/$REGION

echo "Bootstrap complete!"
