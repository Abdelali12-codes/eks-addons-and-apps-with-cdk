# Project Structure

```
eks-addons-and-apps-with-cdk/
│
├── .github/                    # GitHub workflows and actions
│   └── workflows/
│       └── main.yaml          # CI/CD pipeline
│
├── config/                     # Configuration files
│   ├── helm-values/           # Helm chart values
│   │   ├── ingress-nginx-helm-values.yaml
│   │   └── values.yaml
│   └── template.yaml          # CloudFormation template
│
├── docs/                       # Documentation
│   ├── ADDONS.md              # EKS addons documentation
│   ├── APPLICATIONS.md        # Applications documentation
│   ├── ARCHITECTURE.md        # Architecture overview
│   ├── OPENSEARCH.md          # OpenSearch setup guide
│   ├── SETUP.md               # Setup instructions
│   └── nginx.md               # NGINX configuration
│
├── eks_python/                 # Main CDK application (Python package)
│   ├── addons/                # EKS addons
│   │   ├── custom_resources/  # Custom resource handlers
│   │   ├── argocd.py
│   │   ├── cert_manager.py
│   │   ├── dashboard.py
│   │   ├── ebs_driver.py
│   │   ├── efs_driver.py
│   │   ├── eks_auth.py
│   │   ├── external_dns.py
│   │   ├── external_secret.py
│   │   ├── karpenter.py
│   │   ├── keda.py
│   │   ├── nginx_ingress.py
│   │   ├── opentelemetry.py
│   │   ├── s3_driver.py
│   │   └── traefik_ingress.py
│   │
│   ├── application/           # Kubernetes applications
│   │   ├── airflow/          # Apache Airflow
│   │   ├── database_k8s_operator/  # Database operator
│   │   ├── ebs_eks/          # EBS examples
│   │   ├── flaskapp/         # Flask application
│   │   ├── k8s_operator/     # Kubernetes operator
│   │   ├── k8s_secret_aws/   # AWS Secrets integration
│   │   ├── k8s_serviceaccount/  # Service account examples
│   │   ├── prometheus-metrics-demo/  # Prometheus demo
│   │   ├── airflow.py
│   │   ├── elasticsearch_operator.py
│   │   ├── fluent_bit.py
│   │   ├── jenkins.py
│   │   ├── keycloak.py
│   │   ├── locust.py
│   │   ├── openmetadata.py
│   │   └── main.py
│   │
│   ├── configuration/         # Configuration management
│   │   └── config.py         # Main configuration
│   │
│   ├── policies/              # IAM policies
│   │   ├── alb_policy.json
│   │   ├── ebs_policy.json
│   │   ├── efs_policy.json
│   │   ├── external_dns_policy.json
│   │   └── main.py
│   │
│   ├── resources/             # AWS resources
│   │   ├── custom_resources_cdk/  # Custom CDK resources
│   │   ├── client_vpn.py
│   │   ├── opensearch.py
│   │   ├── rdsdatabase.py
│   │   ├── route53.py
│   │   ├── secrets.py
│   │   └── vpc.py
│   │
│   └── eks_python_stack.py    # Main CDK stack
│
├── examples/                   # Example configurations
│   ├── helm-tutorials/        # Helm tutorials
│   └── kratix/               # Kratix examples
│
├── scripts/                    # Utility scripts
│   ├── bootstrap.sh          # CDK bootstrap script
│   └── update-kubeconfig.sh  # Kubeconfig update script
│
├── tests/                      # Test files
│   ├── dags/                 # Airflow DAG tests
│   ├── unit/                 # Unit tests
│   └── __init__.py
│
├── .editorconfig              # Editor configuration
├── .gitignore                 # Git ignore rules
├── app.py                     # CDK app entry point
├── cdk.context.json           # CDK context
├── cdk.json                   # CDK configuration
├── CHANGELOG.md               # Version history
├── CONTRIBUTING.md            # Contribution guidelines
├── LICENSE                    # MIT License
├── Makefile                   # Development tasks
├── pyproject.toml            # Python project configuration
├── README.md                  # Project documentation
├── requirements.txt           # Python dependencies
├── requirements-dev.txt       # Development dependencies
└── setup.py                   # Package setup
```

## Naming Conventions

### Directories
- **Python packages**: `snake_case` (e.g., `eks_python/`, `custom_resources/`)
- **Documentation**: `lowercase` (e.g., `docs/`, `scripts/`)
- **Examples**: `kebab-case` (e.g., `helm-tutorials/`)

### Files
- **Python files**: `snake_case.py` (e.g., `eks_python_stack.py`)
- **Configuration files**: `kebab-case.yaml` or `kebab-case.json`
- **Documentation**: `UPPERCASE.md` for root docs, `PascalCase.md` for nested docs
- **Scripts**: `kebab-case.sh`

### Python Code
- **Classes**: `PascalCase` (e.g., `EksPythonStack`)
- **Functions/Methods**: `snake_case` (e.g., `create_cluster()`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `CLUSTER_NAME`)
- **Variables**: `snake_case` (e.g., `node_group`)
