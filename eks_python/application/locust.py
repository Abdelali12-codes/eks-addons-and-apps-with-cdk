from aws_cdk import (Resource, RemovalPolicy, CfnDynamicReference, Fn, Stack, CfnDynamicReferenceService)
from jinja2 import Environment, FileSystemLoader
import aws_cdk.aws_eks  as eks
import textwrap
import os
from ..configuration.config import *

DIR = os.path.dirname(os.path.realpath(__file__))


class Locust(Resource):
    def __init__(self, scope, id, cluster: eks.ICluster, **kwargs):
        super().__init__(scope, id)
        locustnamespace = eks.KubernetesManifest(
                self,
                "locustnamespace",
                cluster=cluster,
                manifest=[{
                       "apiVersion": "v1",
                       "kind": "Namespace",
                       "metadata": {"name": "locust"}
                }]
            )
                    
        locustconfigmap = eks.KubernetesManifest(
                self,
                "externalsecretnamespace",
                cluster=cluster,
                manifest=[{
                    "apiVersion": "v1",
                    "kind": "ConfigMap",
                    "metadata": {
                        "name": "locust-file",
                        "namespace": "locust"
                    },
                    "data": {
                        "locustfile.py": textwrap.dedent("""\
                            from locust import HttpUser, task, between

                            default_headers = {
                                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_4) '
                                            'AppleWebKit/537.36 (KHTML, like Gecko) '
                                            'Chrome/76.0.3809.100 Safari/537.36'
                            }

                            class WebsiteUser(HttpUser):
                                wait_time = between(1, 5)

                                @task(1)
                                def get_index(self):
                                    self.client.get("/", headers=default_headers)
                            """).strip()
                    }
                }]
        )
        locustconfigmap.node.add_dependency(locustnamespace)
        locusthelm = eks.HelmChart(self, "locust-helm-chart",
                      cluster= cluster,
                      namespace= "locust",
                      create_namespace=False,
                      repository="https://charts.deliveryhero.io/",
                      release="locust",
                      wait=False,
                      chart="locust",
                      values= {
                          "loadtest":{
                            "name": "locust",
                            "locust_locustfile": "locustfile.py",
                            "locust_locustfile_path": "/mnt/locust",
                            "locust_locustfile_configmap": "locust-file",
                            "locust_lib_configmap": "example-lib",
                            "locust_host": "https://www.google.com",
                            "locustCmd": "/opt/venv/bin/locust"
                          }
                      }
                      
                    )

        locustingress = eks.KubernetesManifest(
                self,
                "locustingress",
                cluster=cluster,
                manifest=[{
                    "apiVersion": "networking.k8s.io/v1",
                    "kind": "Ingress",
                    "metadata": {
                        "name": "locust-ingress",
                        "namespace": "locust",
                        "annotations": {
                        "cert-manager.io/cluster-issuer": "dns-01-production"
                        }
                    },
                    "spec": {
                        "ingressClassName": "ingress-nginx",
                        "rules": [
                        {
                            "host": "locust.abdelalitraining.com",
                            "http": {
                            "paths": [
                                {
                                "pathType": "Prefix",
                                "path": "/",
                                "backend": {
                                    "service": {
                                    "name": "locust",
                                    "port": {
                                        "number": 8089
                                    }
                                    }
                                }
                                }
                            ]
                            }
                        }
                        ],
                        "tls": [
                        {
                            "hosts": [
                            "locust.abdelalitraining.com"
                            ],
                            "secretName": "locust-abdelalitraining-com"
                        }
                        ]
                    }
                    }
                ]
            )
        locustingress.node.add_dependency(locusthelm)
        locustconfigmap.node.add_dependency(locustnamespace)
        locusthelm.node.add_dependency(locustnamespace)
