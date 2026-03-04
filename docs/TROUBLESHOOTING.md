# Troubleshooting Guide

## CDK Version Mismatch

### Error: Cloud assembly schema version mismatch

```
Maximum schema version supported is 41.x.x, but found 48.0.0
```

**Solution:**

Option 1 - Upgrade CDK CLI (Recommended):
```bash
npm install -g aws-cdk@latest
cdk --version
```

Option 2 - Downgrade CDK Library:
```bash
pip install aws-cdk-lib==2.170.0
```

### Verify Compatibility

```bash
# Check CLI version
cdk --version

# Check library version
pip show aws-cdk-lib
```

## Common Issues

### Bootstrap Error

**Error:** Stack is not bootstrapped

**Solution:**
```bash
cdk bootstrap aws://ACCOUNT_ID/REGION
```

### Authentication Error

**Error:** Unable to locate credentials

**Solution:**
```bash
aws configure
# Or set environment variables
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

### Dependency Conflicts

**Solution:**
```bash
pip install --upgrade -r requirements.txt
```

### Node Version Issues

**Solution:**
```bash
# Use Node.js 18+ LTS
nvm install 18
nvm use 18
```
