# Applications Documentation

## Airflow
Apache Airflow for workflow orchestration.

**Access**: `https://airflow.YOUR_DOMAIN.com`

**Configuration**: Helm chart with custom values

## Jenkins
CI/CD automation server.

**Access**: `https://jenkins.YOUR_DOMAIN.com`

**Storage**: EFS for shared workspace

## Keycloak
Open source identity and access management.

**Access**: `https://keycloak.YOUR_DOMAIN.com`

**Configuration**: 
```
http://<host>:<port>/auth/realms/<realm_name>/.well-known/openid-configuration
```

## OpenMetadata
Unified metadata platform for data discovery.

**Access**: `https://openmetadata.YOUR_DOMAIN.com`

**Default Credentials**:
- Username: `admin@open-metadata.org`
- Password: `admin`

## FluentBit
Log aggregation and forwarding to OpenSearch.

**Configuration**: DaemonSet on all nodes

## Locust
Load testing tool.

**Access**: `https://locust.YOUR_DOMAIN.com`
