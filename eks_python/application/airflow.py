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
    
        # EbsDriverServicea(self, cluster=cluster)
        # airflowhelm = eks.HelmChart(self, "airflow-helm-chart",
        #               cluster= cluster,
        #               namespace= "airflow",
        #               create_namespace=True,
        #               repository="https://airflow.apache.org",
        #               release="airflow",
        #               wait=False,
        #               chart="airflow",
        #               values= {
        #                     "postgresql": {
        #                       "enabled": False
        #                     },
        #                     "ingress": {
        #                        "web": {
        #                            "enabled": True,
        #                            "annotations": {
        #                                "cert-manager.io/cluster-issuer": "dns-01-production"
        #                            },
        #                            "hosts": [
        #                                {
        #                                    "name": "airflow.abdelalitraining.com",
        #                                    "tls": {
        #                                         "enabled": True,
        #                                         "secretName": "airflow-abdelalitraining-com"
        #                                     }
        #                                }
        #                            ],
        #                        }
        #                     },
        #                     "trigger": {
        #                         "persistence": {
        #                             "enabled": False
        #                         }
        #                     },
        #                     "workers": {
        #                         "persistence": {
        #                             "storageClassName": "ebs-sc",
        #                             "size": "10Gi"
        #                         }
        #                     },
        #                     "redis": {
        #                         "persistence": {
        #                             "storageClassName": "ebs-sc"
        #                         }
        #                     },
        #                     "dags": {
        #                         "persistence": {
        #                             "enabled": True,
        #                             "storageClassName": "ebs-sc"
        #                         }
        #                     }
        #               }
                      
        #             )
        
        username = CfnDynamicReference(CfnDynamicReferenceService.SECRETS_MANAGER,
                                              f"{secret.secret_name}:SecretString:username").to_string()
        
        password = CfnDynamicReference(CfnDynamicReferenceService.SECRETS_MANAGER,
                                              f"{secret.secret_name}:SecretString:password").to_string()
        
        host = CfnDynamicReference(CfnDynamicReferenceService.SECRETS_MANAGER,
                                              f"{secret.secret_name}:SecretString:host").to_string()
        
        dbname = CfnDynamicReference(CfnDynamicReferenceService.SECRETS_MANAGER,
                                              f"{secret.secret_name}:SecretString:dbname").to_string()
        

        databaseSecret = eks.KubernetesManifest(
                self,
                "databaseSecret",
                cluster=cluster,
                manifest=[{
                    "apiVersion": "v1",
                    "kind": "Secret",
                    "metadata": {
                        "name": "airflow-metadata-secret",
                        "namespace": "airflow"
                    },
                    "stringData": {
                        "connection": f"postgresql://{username}:{password}@{host}:5432/{dbname}?sslmode=disable"
                    },
                    "type": "Opaque"
                    }
                ]
        )
        # databaseSecret.node.add_dependency(airflowhelm)