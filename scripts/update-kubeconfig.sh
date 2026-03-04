#!/bin/bash
set -e

CLUSTER_NAME=${1:-""}
REGION=${2:-$(aws configure get region)}

if [ -z "$CLUSTER_NAME" ]; then
    echo "Usage: $0 <cluster-name> [region]"
    exit 1
fi

echo "Updating kubeconfig for cluster: $CLUSTER_NAME in region: $REGION"
aws eks update-kubeconfig --name $CLUSTER_NAME --region $REGION

echo "Verifying cluster access..."
kubectl get nodes
kubectl get pods -A

echo "Kubeconfig updated successfully!"
