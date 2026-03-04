# EKS Addons and Applications with AWS CDK

Production-ready AWS CDK project for deploying Amazon EKS cluster with essential addons and applications.

## Features

- **EKS Cluster**: Managed Kubernetes cluster with IRSA support
- **Networking**: VPC with public/private subnets, NAT gateways
- **Storage**: EBS, EFS, and S3 CSI drivers
- **Ingress**: NGINX and Traefik ingress controllers
- **GitOps**: ArgoCD for continuous delivery
- **Observability**: OpenTelemetry, Prometheus, FluentBit, OpenSearch
- **Autoscaling**: Karpenter and KEDA
- **Applications**: Airflow, Jenkins, Keycloak, OpenMetadata
- **Security**: Cert Manager, External Secrets, IAM roles

## Quick Start

```bash
# Clone repository
git clone <repository-url>
cd eks-addons-and-apps-with-cdk

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate.bat

# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
aws configure

# Bootstrap CDK (first time only)
cdk bootstrap

# Deploy
cdk deploy --all
```

## Project Structure

```
├── eks_python/              # Main CDK application (Python package)
│   ├── addons/             # EKS addons (ArgoCD, Cert Manager, etc.)
│   ├── application/        # Kubernetes applications (Airflow, Jenkins, etc.)
│   ├── configuration/      # Configuration management
│   ├── policies/           # IAM policies (JSON)
│   └── resources/          # AWS resources (VPC, RDS, OpenSearch)
├── config/                 # Configuration files (Helm values, templates)
├── docs/                   # Documentation (Architecture, Setup, etc.)
├── examples/               # Example configurations (Helm, Kratix)
├── scripts/                # Utility scripts (Bootstrap, Kubeconfig)
├── tests/                  # Test files (Unit, Integration)
└── app.py                  # CDK app entry point
```

See [Project Structure](docs/PROJECT_STRUCTURE.md) for detailed information.

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md)
- [Setup Guide](docs/SETUP.md)
- [Project Structure](docs/PROJECT_STRUCTURE.md)
- [Addons Documentation](docs/ADDONS.md)
- [Applications Documentation](docs/APPLICATIONS.md)
- [OpenSearch Setup](docs/OPENSEARCH.md)

## Configuration

Edit `eks_python/configuration/config.py`:

```python
ACCOUNT = "123456789012"
REGION = "us-east-1"
CLUSTER_NAME = "my-eks-cluster"
DOMAIN_NAME = "example.com"
```

## Common Commands

```bash
# List all stacks
cdk ls

# Synthesize CloudFormation template
cdk synth

# Deploy all stacks
cdk deploy --all

# Show differences
cdk diff

# Destroy all stacks
cdk destroy --all

# Run tests
pytest tests/

# Update kubeconfig
aws eks update-kubeconfig --name CLUSTER_NAME --region REGION
```

## Makefile Commands

```bash
make install    # Install dependencies
make synth      # Synthesize template
make deploy     # Deploy to AWS
make destroy    # Destroy stacks
make test       # Run tests
make lint       # Run linting
make format     # Format code
make clean      # Clean artifacts
```

## Prerequisites

- Python 3.8+
- Node.js 14+
- AWS CLI configured
- AWS CDK CLI: `npm install -g aws-cdk`
- kubectl

## Addons

| Addon | Description |
|-------|-------------|
| ArgoCD | GitOps continuous delivery |
| Cert Manager | Certificate management |
| External DNS | DNS management |
| NGINX Ingress | Ingress controller |
| EBS CSI Driver | Block storage |
| EFS CSI Driver | File storage |
| Karpenter | Node autoscaling |
| KEDA | Event-driven autoscaling |
| OpenTelemetry | Observability |

## Applications

| Application | Description |
|-------------|-------------|
| Airflow | Workflow orchestration |
| Jenkins | CI/CD automation |
| Keycloak | Identity management |
| OpenMetadata | Data catalog |
| FluentBit | Log aggregation |

## Security

- IRSA (IAM Roles for Service Accounts)
- Secrets Manager integration
- Network policies
- Pod security standards
- TLS/SSL certificates

## Monitoring

- Prometheus metrics
- OpenSearch logging
- AWS X-Ray tracing
- CloudWatch integration

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

MIT License

## Support

For issues and questions, please open a GitHub issue.
