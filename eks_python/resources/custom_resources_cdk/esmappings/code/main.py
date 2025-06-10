import json
import boto3
import requests
import os
from requests.auth import HTTPBasicAuth

# Configuration
secret_name = os.getenv("SECRET_NAME")
region_name = os.getenv("REGION_NAME")
opensearch_endpoint = os.getenv("OPENSEARCH_ENDPOINT")
role_name = os.getenv("ROLE_NAME")


def get_credentials():
    """Fetch credentials from Secrets Manager"""
    client = boto3.client('secretsmanager', region_name=region_name)
    secret = client.get_secret_value(SecretId=secret_name)
    secret_dict = json.loads(secret['SecretString'])
    return secret_dict['username'], secret_dict['password']


def handler(event, context):
    # Get credentials
    username, password = get_credentials()

    # Role mapping payload
    payload = {
        "backend_roles": [
            role_name
        ],
        "hosts": [],
        "users": []
    }

    headers = {"Content-Type": "application/json"}
    url = f"https://{opensearch_endpoint}/_opendistro/_security/api/rolesmapping/all_access?pretty"

    response = requests.put(
        url,
        headers=headers,
        auth=HTTPBasicAuth(username, password),
        data=json.dumps(payload),
        timeout=10,
        verify=True  # Set to False only for testing/self-signed certs
    )

    return {
        "statusCode": response.status_code,
        "body": response.text
    }
