from aws_cdk import (Resource, RemovalPolicy, CfnDynamicReference, Fn, Stack, CfnDynamicReferenceService)
from jinja2 import Environment, FileSystemLoader
import aws_cdk.aws_eks  as eks
import aws_cdk.aws_rds as rds
import aws_cdk.aws_secretsmanager as sm
import aws_cdk.aws_s3 as s3
from ..policies.main import AirflowServiceAccount
import os
from ..configuration.config import *

DIR = os.path.dirname(os.path.realpath(__file__))


class Openmetadata(Resource):
    def __init__(self, scope, id, cluster: eks.ICluster, db , elasticsearch, airflow , **kwargs):
        super().__init__(scope, id)
    
        openmetadatanamespace = eks.KubernetesManifest(
                self,
                "openmetadatanamespace",
                cluster=cluster,
                manifest=[{
                       "apiVersion": "v1",
                       "kind": "Namespace",
                       "metadata": {"name": "openmetadata"}
                }]
            )
        
        openmetadatahelm = eks.HelmChart(self, "openmetada-helm-chart",
                      cluster= cluster,
                      namespace= "openmetadata",
                      create_namespace=False,
                      repository="https://helm.open-metadata.org/",
                      release="openmetadata",
                      wait=False,
                      chart="openmetadata",
                      values= {
                            "openmetadata": {
                                "config": {
                                    "elasticsearch": {
                                        "host": elasticsearch.domain_endpoint,
                                        "searchType": "elasticsearch",
                                        "port": 443,
                                        "scheme": "https",
                                        "auth": {
                                            "enabled": True,
                                            "username": "master",
                                            "password": {
                                                "secretRef": "elasticsearch-secret",
                                                "secretKey": "password"
                                            }
                                        }
                                    },
                                    "database": {
                                        "host": db.rds_endpoint,
                                        "port": 5432,
                                        "driverClass": "org.postgresql.Driver",
                                        "dbScheme": "postgresql",
                                        "databaseName": "openmetadata",
                                        "auth": {
                                            "username": "openmetadata",
                                            "password": {
                                                "secretRef": "database-secret",
                                                "secretKey": "password"
                                            }
                                        }
                                    },
                                    "pipelineServiceClientConfig": {
                                        "apiEndpoint": "http://airflow-webserver.airflow.svc:8080",
                                        "auth": {
                                            "username": "airflow",
                                            "password": {
                                                "secretRef": "airflow-secret",
                                                "secretKey": "password"
                                            }
                                        }
                                    }
                                }
                            },
                            "ingress": {
                                "enabled": True,
                                "className": "ingress-nginx",
                                "annotations": {
                                       "cert-manager.io/cluster-issuer": "dns-01-production"
                                },
                                "hosts": [
                                       {
                                           "host": "openmetadata.abdelalitraining.com",
                                           "paths": [
                                               {
                                                   "path": "/",
                                                   "pathType": "ImplementationSpecific"
                                               }
                                           ]
                                       }
                                   ],
                                "tls": [
                                    {
                                        "secretName": "openmetadata-abdelalitraining-com",
                                        "hosts": [
                                            "openmetadata.abdelalitraining.com"
                                        ]
                                    }
                                ]
                            }
                        }
        )

        databaseSecret = eks.KubernetesManifest(
                self,
                "databaseSecret",
                cluster=cluster,
                manifest=[{
                    "apiVersion": "external-secrets.io/v1",
                    "kind": "ExternalSecret",
                    "metadata": {
                        "name": "database-secret",
                        "namespace": "openmetadata"
                    },
                    "spec": {
                        "refreshInterval": "1h",
                        "secretStoreRef": {
                            "name": "aws-secrets-manager",
                            "kind": "ClusterSecretStore"
                        },
                        "target": {
                            "name": "database-secret",
                            "template": {
                                "type": "Opaque",
                                "data": {
                                    "password": "{{ .password }}"
                                }
                            }
                        },
                        "dataFrom": [
                        {
                            "extract": {
                                "key": db.dbsecret.secret_name
                            }
                        }
                        ]
                    }
                }
            ]
        )

        elasticsearchSecret = eks.KubernetesManifest(
                self,
                "elasticsearchSecret",
                cluster=cluster,
                manifest=[{
                    "apiVersion": "external-secrets.io/v1",
                    "kind": "ExternalSecret",
                    "metadata": {
                        "name": "elasticsearch-secret",
                        "namespace": "openmetadata"
                    },
                    "spec": {
                        "refreshInterval": "1h",
                        "secretStoreRef": {
                            "name": "aws-secrets-manager",
                            "kind": "ClusterSecretStore"
                        },
                        "target": {
                            "name": "elasticsearch-secret",
                            "template": {
                                "type": "Opaque",
                                "data": {
                                    "password": "{{ .password }}"
                                }
                            }
                        },
                        "dataFrom": [
                        {
                            "extract": {
                                "key": elasticsearch.essecret.secret_name
                            }
                        }
                        ]
                    }
                }
            ]
        )

        airflowSecret = eks.KubernetesManifest(
                self,
                "airflowSecret",
                cluster=cluster,
                manifest=[{
                    "apiVersion": "external-secrets.io/v1",
                    "kind": "ExternalSecret",
                    "metadata": {
                        "name": "airflow-secret",
                        "namespace": "openmetadata"
                    },
                    "spec": {
                        "refreshInterval": "1h",
                        "secretStoreRef": {
                            "name": "aws-secrets-manager",
                            "kind": "ClusterSecretStore"
                        },
                        "target": {
                            "name": "airflow-secret",
                            "template": {
                                "type": "Opaque",
                                "data": {
                                    "password": "{{ .AIRFLOW_PASSWORD }}"
                                }
                            }
                        },
                        "dataFrom": [
                        {
                            "extract": {
                                "key": airflow.airflowsecret.secret_name
                            }
                        }
                        ]
                    }
                }
            ]
        )
        airflowSecret.node.add_dependency(openmetadatanamespace)
        databaseSecret.node.add_dependency(openmetadatanamespace)
        elasticsearchSecret.node.add_dependency(openmetadatanamespace)
        airflowSecret.node.add_dependency(openmetadatahelm)
        databaseSecret.node.add_dependency(openmetadatahelm)
        elasticsearchSecret.node.add_dependency(openmetadatahelm)
