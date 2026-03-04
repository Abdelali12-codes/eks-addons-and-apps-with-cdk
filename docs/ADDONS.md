# EKS Addons Documentation

## ArgoCD
GitOps continuous delivery tool for Kubernetes.

**Access**: `https://argocd.YOUR_DOMAIN.com`

**Default Credentials**: Retrieved from Kubernetes secret

## Cert Manager
Automates certificate management in Kubernetes.

**Configuration**: Supports Let's Encrypt and other ACME providers

## External DNS
Automatically manages DNS records for Kubernetes resources.

**Supported Providers**: Route53, CloudFlare, etc.

## Ingress Controllers

### NGINX Ingress
High-performance ingress controller.

### Traefik Ingress
Modern HTTP reverse proxy and load balancer.

## Storage Drivers

### EBS CSI Driver
Amazon EBS volumes for persistent storage.

### EFS CSI Driver
Amazon EFS for shared file storage.

### S3 CSI Driver
Mount S3 buckets as volumes.

## Autoscaling

### Karpenter
Just-in-time node provisioning for Kubernetes.

### KEDA
Kubernetes Event-driven Autoscaling.

## Observability

### OpenTelemetry
Unified observability framework.

**Backends**: AWS X-Ray, Prometheus

### FluentBit
Log processor and forwarder.

**Destination**: OpenSearch, CloudWatch
