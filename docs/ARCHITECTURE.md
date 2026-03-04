# Architecture Overview

## Project Structure

```
eks-addons-and-apps-with-cdk/
├── eks_python/              # Main CDK application code
│   ├── addons/             # EKS addons (ArgoCD, Cert Manager, etc.)
│   ├── application/        # Kubernetes applications
│   ├── configuration/      # Configuration management
│   ├── policies/           # IAM policies
│   └── resources/          # AWS resources (VPC, RDS, etc.)
├── docs/                   # Documentation
├── scripts/                # Utility scripts
├── config/                 # Configuration files
├── tests/                  # Test files
└── app.py                  # CDK app entry point
```

## Components

### EKS Cluster
- Managed node groups
- IRSA (IAM Roles for Service Accounts)
- VPC with public/private subnets

### Addons
- ArgoCD - GitOps continuous delivery
- Cert Manager - Certificate management
- External DNS - DNS management
- NGINX/Traefik Ingress - Ingress controllers
- EBS/EFS CSI Drivers - Storage
- Karpenter - Node autoscaling
- KEDA - Event-driven autoscaling
- OpenTelemetry - Observability

### Applications
- Airflow - Workflow orchestration
- Jenkins - CI/CD
- Keycloak - Identity management
- OpenMetadata - Data catalog
- FluentBit - Log aggregation

## AWS Resources
- VPC with NAT Gateways
- RDS databases
- OpenSearch for logging
- Route53 for DNS
- Secrets Manager for credentials
