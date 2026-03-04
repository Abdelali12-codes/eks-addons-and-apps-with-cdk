# Setup Guide

## Prerequisites

- Python 3.8+
- Node.js 14+
- AWS CLI configured
- AWS CDK CLI installed (`npm install -g aws-cdk`)
- kubectl installed

## Installation

1. Clone the repository
2. Create and activate virtual environment:

```bash
# Windows
python -m venv .venv
.venv\Scripts\activate.bat

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

4. Configure AWS credentials:

```bash
aws configure
```

5. Bootstrap CDK (first time only):

```bash
cdk bootstrap aws://ACCOUNT-ID/REGION
```

## Configuration

Edit `eks_python/configuration/config.py` to set:
- AWS Account ID
- AWS Region
- Cluster name
- VPC CIDR ranges
- Domain names

## Deployment

```bash
# Synthesize CloudFormation template
cdk synth

# Deploy all stacks
cdk deploy --all

# Deploy specific stack
cdk deploy EksPythonStack
```

## Post-Deployment

1. Update kubeconfig:

```bash
aws eks update-kubeconfig --name YOUR_CLUSTER_NAME --region YOUR_REGION
```

2. Verify cluster access:

```bash
kubectl get nodes
kubectl get pods -A
```

## Cleanup

```bash
cdk destroy --all
```
