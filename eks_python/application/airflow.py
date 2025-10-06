from aws_cdk import (Resource, RemovalPolicy, CfnDynamicReference, Fn, Stack, CfnDynamicReferenceService)
from jinja2 import Environment, FileSystemLoader
import aws_cdk.aws_eks  as eks
import aws_cdk.aws_secretsmanager as sm
import json
import yaml
import aws_cdk.aws_s3 as s3
from ..policies.main import AirflowServiceAccount
import os
from ..configuration.config import *

DIR = os.path.dirname(os.path.realpath(__file__))


class Airflow(Resource):
    def __init__(self, scope, id, cluster: eks.ICluster, secret: sm.ISecret,  **kwargs):
        super().__init__(scope, id)


        self.airflowsecret = sm.Secret(self, "airflow-secret",
                                      secret_name="airflow-secret",
                                      generate_secret_string=sm.SecretStringGenerator(
                                          secret_string_template=json.dumps({
                                              "AIRFLOW_USERNAME": "airflow",
                                              "AIRFLOW_FIRSTNAME": "airflow",
                                              "AIRFLOW_LASTNAME": "airflow",
                                              "AIRFLOW_EMAIL": "airflow@example.com"
                                            }),
                                          exclude_punctuation=False,
                                          password_length=16,
                                          generate_string_key="AIRFLOW_PASSWORD"
                                      )
                                      )
    
        extraenvFrom = yaml.dump([
            {
                "secretRef": {
                    "name": "airflow-secret"
                }
            }
        ])
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
        airflowloggingbucket = s3.Bucket(self, "airflowloggingbucket",
                      bucket_name="airflow-logging-bucket-24-09-2025",
                      removal_policy= RemovalPolicy.DESTROY              
                    )
        airflowsa = AirflowServiceAccount(self, cluster=cluster)
        airflowhelm = eks.HelmChart(self, "airflow-helm-chart",
                      cluster= cluster,
                      namespace= "airflow",
                      create_namespace=False,
                      repository="https://airflow.apache.org",
                      release="airflow",
                      wait=False,
                      chart="airflow",
                      values= {
                            "airflowVersion": "2.11.0",
                            "defaultAirflowTag": "2.11.0",
                            "airflowLocalSettings": """
                                {{- if semverCompare ">=2.2.0 <3.0.0" .Values.airflowVersion }}
                                {{- if not (or .Values.webserverSecretKey .Values.webserverSecretKeySecretName) }}
                                print("airflow")
                                {{- end }}
                                {{- end }}
                                """
                            ,
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
                                   "ingressClassName": "ingress-nginx"
                               }
                            },
                            "createUserJob": {
                                "useHelmHooks": False,
                                "applyCustomEnv": True,
                                "args": [
                                    "bash",
                                    "-c",
                                    "exec airflow users create -r Admin -u \"${AIRFLOW_USERNAME}\" -e \"${AIRFLOW_EMAIL}\" -f \"${AIRFLOW_FIRSTNAME}\" -l \"${AIRFLOW_LASTNAME}\" -p \"${AIRFLOW_PASSWORD}\""
                                ]
                            },
                            "migrateDatabaseJob": {
                                # "enabled": False,
                                "useHelmHooks": False,
                                "applyCustomEnv": False
                            },
                            "data": {
                              "metadataSecretName": "airflow-metadata-secret",
                              "resultBackendSecretName": "airflow-backendresult-secret"
                            },
                            "extraEnvFrom": extraenvFrom,
                            "triggerer": {
                                "persistence": {
                                    "enabled": False
                                }
                            },
                            "webserver": {
                                "serviceAccount": {
                                    "create": False,
                                    "name": "airflow-sa",
                                    "annotations": {
                                        "eks.amazonaws.com/role-arn": airflowsa.role_arn
                                    }
                                }
                            },
                            "workers": {
                                "serviceAccount": {
                                    "create": False,
                                    "name": "airflow-sa",
                                    "annotations": {
                                        "eks.amazonaws.com/role-arn": airflowsa.role_arn
                                    }
                                },
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
                                },
                                "gitSync": {
                                    "enabled": True,
                                    "repo": "https://github.com/Abdelali12-codes/eks-addons-and-apps-with-cdk.git",
                                    "branch": "master",
                                    "rev": "HEAD",
                                    "ref": "master",
                                    "depth": 1,
                                    "subPath": "tests/dags"
                                }
                            },

                            "config": {
                                "logging": {
                                    "remote_logging": True,
                                    "logging_level": "INFO",
                                    "remote_base_log_folder": f"s3://{airflowloggingbucket.bucket_name}/airflow",
                                    "remote_log_conn_id": "aws_conn",
                                    "delete_worker_pods": False,
                                    "encrypt_s3_logs": True
                                },
                                "metrics": {
                                    "otel_on": True,
                                    "otel_host": "otel.abdelalitraining.com",
                                    "otel_port": 80,
                                    "otel_prefix": "airflow",
                                    "otel_interval_milliseconds": 30000,
                                    "otel_ssl_active": False
                                }
                            },
                      }
                      
                    )
        
        airflowmetadataSecret = eks.KubernetesManifest(
                self,
                "metadataSecret",
                cluster=cluster,
                manifest=[{
                    "apiVersion": "external-secrets.io/v1",
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
                "backendresultSecret",
                cluster=cluster,
                manifest=[{
                    "apiVersion": "external-secrets.io/v1",
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

        airflowSecret = eks.KubernetesManifest(
                self,
                "airflowSecret",
                cluster=cluster,
                manifest=[{
                    "apiVersion": "external-secrets.io/v1",
                    "kind": "ExternalSecret",
                    "metadata": {
                        "name": "airflow-secret",
                        "namespace": "airflow"
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
                                    "AIRFLOW_USERNAME": "{{ .AIRFLOW_USERNAME }}",
                                    "AIRFLOW_PASSWORD": "{{ .AIRFLOW_PASSWORD }}",
                                    "AIRFLOW_FIRSTNAME": "{{ .AIRFLOW_FIRSTNAME }}",
                                    "AIRFLOW_LASTNAME": "{{ .AIRFLOW_LASTNAME }}",
                                    "AIRFLOW_EMAIL": "{{ .AIRFLOW_EMAIL }}"
                               }
                            }
                        },
                        "dataFrom": [
                        {
                            "extract": {
                                "key": self.airflowsecret.secret_name
                            }
                        }
                        ]
                    }
                }
            ]
        )
        airflowhelm.node.add_dependency(airflownamespace)
        airflowhelm.node.add_dependency(self.airflowsecret)
        airflowhelm.node.add_dependency(airflowSecret)
        airflowSecret.node.add_dependency(self.airflowsecret)
        airflowSecret.node.add_dependency(airflownamespace)
        airflowbackendresultSecret.node.add_dependency(airflowhelm)
        airflowbackendresultSecret.node.add_dependency(airflownamespace)
        airflowmetadataSecret.node.add_dependency(airflowhelm)
        airflowmetadataSecret.node.add_dependency(airflownamespace)
        airflowsa.node.add_dependency(airflownamespace)