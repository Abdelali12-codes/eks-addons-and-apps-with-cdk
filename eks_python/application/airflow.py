from aws_cdk import (Resource, CfnDynamicReference, Fn, Stack, CfnDynamicReferenceService)
from jinja2 import Environment, FileSystemLoader
import aws_cdk.aws_eks  as eks
import aws_cdk.aws_secretsmanager as sm
from ..policies.main import FluentBitSaRole
import os
from ..configuration.config import *

DIR = os.path.dirname(os.path.realpath(__file__))


class Airflow(Resource):
    def __init__(self, scope, id, cluster: eks.ICluster, secret: sm.ISecret,  **kwargs):
        super().__init__(scope, id)
    
        airflownamespace = eks.KubernetesManifest(
                self,
                "airflownamespace",
                cluster=cluster,
                manifest=[{
                       "apiVersion": "v1",
                       "kind": "Namespace",
                       "metadata": {"name": "airflow"}
                }]
            )
        airflowhelm = eks.HelmChart(self, "airflow-helm-chart",
                      cluster= cluster,
                      namespace= "airflow",
                      create_namespace=False,
                      repository="https://airflow.apache.org",
                      release="airflow",
                      wait=False,
                      chart="airflow",
                      values= {
                            "postgresql": {
                              "enabled": False
                            },
                            "ingress": {
                               "web": {
                                   "enabled": True,
                                   "annotations": {
                                       "cert-manager.io/cluster-issuer": "dns-01-production"
                                   },
                                   "hosts": [
                                       {
                                           "name": "airflow.abdelalitraining.com",
                                           "tls": {
                                                "enabled": True,
                                                "secretName": "airflow-abdelalitraining-com"
                                            }
                                       }
                                   ],
                               }
                            },
                            "createUserJob": {
                                "useHelmHooks": False,
                                "applyCustomEnv": False
                            },
                            "migrateDatabaseJob": {
                                "enabled": False,
                                "useHelmHooks": False,
                                "applyCustomEnv": False
                            },
                            "data": {
                              "metadataSecretName": "airflow-metadata-secret",
                              "resultBackendSecretName": "airflow-backendresult-secret"
                            },
                            "trigger": {
                                "persistence": {
                                    "enabled": False
                                }
                            },
                            "workers": {
                                "persistence": {
                                    "enabled": False
                                }
                            },
                            "redis": {
                                "persistence": {
                                    "storageClassName": "ebs-sc"
                                }
                            },
                            "dags": {
                                "persistence": {
                                    "enabled": True,
                                    "storageClassName": "ebs-sc"
                                }
                            }
                      }
                      
                    )
        
        airflowmetadataSecret = eks.KubernetesManifest(
                self,
                "databaseSecret",
                cluster=cluster,
                manifest=[{
                    "apiVersion": "external-secrets.io/v1beta1",
                    "kind": "ExternalSecret",
                    "metadata": {
                        "name": "airflow-metadata-secret",
                        "namespace": "airflow"
                    },
                    "spec": {
                        "refreshInterval": "1h",
                        "secretStoreRef": {
                            "name": "aws-secrets-manager",
                            "kind": "ClusterSecretStore"
                        },
                        "target": {
                            "name": "airflow-metadata-secret",
                            "template": {
                                "type": "Opaque",
                                "data": {
                                    "connection": "postgresql://{{ .username }}:{{ .password }}@{{ .host }}:{{ .port }}/{{ .dbname }}?sslmode=disable"
                                }
                            }
                        },
                        "dataFrom": [
                        {
                            "extract": {
                                "key": secret.secret_name
                            }
                        }
                        ]
                    }
                }
            ]
        )

        airflowbackendresultSecret = eks.KubernetesManifest(
                self,
                "databaseSecret",
                cluster=cluster,
                manifest=[{
                    "apiVersion": "external-secrets.io/v1beta1",
                    "kind": "ExternalSecret",
                    "metadata": {
                        "name": "airflow-backendresult-secret",
                        "namespace": "airflow"
                    },
                    "spec": {
                        "refreshInterval": "1h",
                        "secretStoreRef": {
                            "name": "aws-secrets-manager",
                            "kind": "ClusterSecretStore"
                        },
                        "target": {
                            "name": "airflow-backendresult-secret",
                            "template": {
                                "type": "Opaque",
                                "data": {
                                    "connection": "db+postgresql://{{ .username }}:{{ .password }}@{{ .host }}:{{ .port }}/{{ .dbname }}?sslmode=disable"
                               }
                            }
                        },
                        "dataFrom": [
                        {
                            "extract": {
                                "key": secret.secret_name
                            }
                        }
                        ]
                    }
                }
            ]
        )
        airflowhelm.node.add_dependency(airflownamespace)
        airflowbackendresultSecret.node.add_dependency(airflowhelm)
        airflowbackendresultSecret.node.add_dependency(airflownamespace)
        airflowmetadataSecret.node.add_dependency(airflowhelm)
        airflowmetadataSecret.node.add_dependency(airflownamespace)