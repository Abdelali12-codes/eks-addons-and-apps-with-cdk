import boto3
import base64
from kubernetes import client, config
import json
import os


def get_secret(secret_name, region_name="us-east-1"):
    """Retrieve secret from AWS Secrets Manager"""
    session = boto3.session.Session()
    client_sm = session.client(service_name="secretsmanager", region_name=region_name)

    response = client_sm.get_secret_value(SecretId=secret_name)

    if "SecretString" in response:
        secret = response["SecretString"]
    else:
        secret = base64.b64decode(response["SecretBinary"])

    return json.loads(secret)  # return dict


def create_k8s_secret(secret_name, namespace, data_dict):
    """Create or update a Kubernetes secret"""
    # Load in-cluster config (ServiceAccount token)
    config.load_incluster_config()
    v1 = client.CoreV1Api()
    connection = f"postgresql://{data_dict['username']}:{data_dict['password']}@{data_dict['host']}:5432/{data_dict['dbname']}?sslmode=disable"
    # Kubernetes Secret data must be base64-encoded
    data_encoded = {"connection": base64.b64encode(connection.encode()).decode()}

    secret_body = client.V1Secret(
        metadata=client.V1ObjectMeta(name=secret_name, namespace=namespace),
        type="Opaque",
        data=data_encoded,
    )

    try:
        v1.create_namespaced_secret(namespace=namespace, body=secret_body)
        print(f"Secret {secret_name} created in {namespace}")
    except client.exceptions.ApiException as e:
        if e.status == 409:  # Already exists → update it
            v1.replace_namespaced_secret(secret_name, namespace, secret_body)
            print(f"Secret {secret_name} updated in {namespace}")
        else:
            raise


if __name__ == "__main__":
    # Configurable via env vars
    aws_secret_name = os.getenv("AWS_SECRET_NAME", "myapp/credentials")
    k8s_secret_name = os.getenv("K8S_SECRET_NAME", "myapp-secret")
    namespace = os.getenv("K8S_NAMESPACE", "default")
    region = os.getenv("AWS_REGION", "us-east-1")

    # 1. Get values from AWS Secrets Manager
    secret_dict = get_secret(aws_secret_name, region)

    # 2. Create/update Kubernetes Secret
    create_k8s_secret(k8s_secret_name, namespace, secret_dict)
