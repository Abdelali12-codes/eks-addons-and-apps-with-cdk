from aws_cdk import (Resource, Stack, RemovalPolicy)
import aws_cdk.aws_eks as eks
from ..policies.main import ExternalSecretServiceAccount


class ExternalSecret(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)
        
        cluster = None 
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")
        

        ExternalSecretServiceAccount(self, cluster=cluster)
        
        externalsecret = eks.HelmChart(self, "externalsecrethelm",
                      cluster= cluster,
                      namespace= "external-secret",
                      create_namespace=True,
                      repository="https://charts.external-secrets.io",
                      release="external-secrets",
                      wait=True,
                      chart="external-secrets",
                    #   values= {
                    #       "webhook":{
                    #           "port": 9443 
                    #       }
                    #   }
                    )
        
        clustersecretstore= eks.KubernetesManifest(self, "ClusterSecretStoreSM",
                              cluster= cluster,
                              manifest=[{
                                "apiVersion": "external-secrets.io/v1beta1",
                                "kind": "ClusterSecretStore",
                                "metadata":{
                                    "name": "aws-secrets-manager"
                                },
                                "spec":{
                                    "provider": {
                                        "aws": {
                                            "service": "SecretsManager",
                                            "region": Stack.of(self).region,
                                            "auth": {
                                                "jwt": {
                                                    "serviceAccountRef": {
                                                        "name": "external-secret-sa",
                                                        "namespace": "external-secret"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                              }]
                            )
        clusterparameterstore= eks.KubernetesManifest(self, "ClusterSecretStoreSSM",
                              cluster= cluster,
                              manifest=[{
                                "apiVersion": "external-secrets.io/v1beta1",
                                "kind": "ClusterSecretStore",
                                "metadata":{
                                    "name": "aws-parameter-store"
                                },
                                "spec":{
                                    "provider": {
                                        "aws": {
                                            "service": "ParameterStore",
                                            "region": Stack.of(self).region,
                                            "auth": {
                                                "jwt": {
                                                    "serviceAccountRef": {
                                                        "name": "external-secret-sa",
                                                        "namespace": "external-secret"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                              }]
                            )
        clustersecretstore.node.add_dependency(externalsecret)
        clusterparameterstore.node.add_dependency(externalsecret)
