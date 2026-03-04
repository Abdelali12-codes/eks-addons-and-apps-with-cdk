# OpenSearch Setup Guide

## Prerequisites

Export required variables:

```bash
export ES_DOMAIN_NAME="your-app-logging"
export ES_VERSION="OpenSearch_2.7"
export ES_DOMAIN_USER="admin"
export ES_DOMAIN_PASSWORD="$(openssl rand -base64 15)_Ek1$"

echo "OpenSearch Domain: ${ES_DOMAIN_NAME}"
echo "OpenSearch User: ${ES_DOMAIN_USER}"
echo "OpenSearch Password: ${ES_DOMAIN_PASSWORD}"
```

## FluentBit IAM Policy

```bash
cat <<EoF > fluent-bit-policy.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": ["es:ESHttp*"],
            "Resource": "arn:aws:es:REGION:ACCOUNT_ID:domain/${ES_DOMAIN_NAME}",
            "Effect": "Allow"
        }
    ]
}
EoF

aws iam create-policy \
  --policy-name fluent-bit-policy \
  --policy-document file://fluent-bit-policy.json
```

## Service Account

```bash
eksctl create iamserviceaccount \
    --name fluent-bit \
    --namespace logging \
    --cluster YOUR_CLUSTER \
    --attach-policy-arn "arn:aws:iam::ACCOUNT_ID:policy/fluent-bit-policy" \
    --approve \
    --override-existing-serviceaccounts
```

## Configure Role Mapping

```bash
export FLUENTBIT_ROLE=$(kubectl get sa fluent-bit -n logging -o jsonpath='{.metadata.annotations.eks\.amazonaws\.com/role-arn}')
export ES_ENDPOINT=$(aws opensearch describe-domain --domain-name ${ES_DOMAIN_NAME} --output text --query "DomainStatus.Endpoint")

curl -sS -u "${ES_DOMAIN_USER}:${ES_DOMAIN_PASSWORD}" \
    -X PATCH \
    https://${ES_ENDPOINT}/_opendistro/_security/api/rolesmapping/all_access?pretty \
    -H 'Content-Type: application/json' \
    -d '[{"op": "add", "path": "/backend_roles", "value": ["'${FLUENTBIT_ROLE}'"]}]'
```

## Verify

```bash
kubectl get pods -n logging
kubectl logs -n logging -l k8s-app=fluent-bit-logging
```
