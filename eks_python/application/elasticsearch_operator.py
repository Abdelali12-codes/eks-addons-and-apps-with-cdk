from aws_cdk import (Resource, RemovalPolicy, CfnDynamicReference, Fn, Stack, CfnDynamicReferenceService)
from jinja2 import Environment, FileSystemLoader
import aws_cdk.aws_eks  as eks
import aws_cdk.aws_efs as efs
import yaml
import textwrap
import os
from ..configuration.config import *

DIR = os.path.dirname(os.path.realpath(__file__))


class EckOperator(Resource):
    def __init__(self, scope, id, cluster: eks.ICluster, vpc, **kwargs):
        super().__init__(scope, id)

        eckoperatorhelm = eks.HelmChart(self, "eckoperator-helm-chart",
                        cluster= cluster,
                        namespace= "elastic-system",
                        create_namespace=True,
                        repository="https://helm.elastic.co",
                        release="elastic-operator",
                        wait=False,
                        chart="eck-operator"
                    )

        jenkinsingress = eks.KubernetesManifest(
                self,
                "jenkinsingress",
                cluster=cluster,
                manifest=[{
                    "apiVersion": "networking.k8s.io/v1",
                    "kind": "Ingress",
                    "metadata": {
                        "name": "jenkins-ingress",
                        "namespace": "jenkins",
                        "annotations": {
                        "cert-manager.io/cluster-issuer": "dns-01-production"
                        }
                    },
                    "spec": {
                        "ingressClassName": "ingress-nginx",
                        "rules": [
                        {
                            "host": "jenkins.abdelalitraining.com",
                            "http": {
                            "paths": [
                                {
                                "pathType": "Prefix",
                                "path": "/",
                                "backend": {
                                    "service": {
                                    "name": "jenkins",
                                    "port": {
                                        "number": 80
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
                            "jenkins.abdelalitraining.com"
                            ],
                            "secretName": "jenkins-abdelalitraining-com"
                        }
                        ]
                    }
                    }
                ]
            )
        env = Environment(loader=FileSystemLoader(DIR))
        template = env.get_template('jenkins_pvc.yaml.j2')
        rendered_template = template.render({
            "efs_access_point": efs_access_point.access_point_id
        })

        documents = yaml.load_all(rendered_template)    
        for index, manifest in enumerate(documents):
                cluster.add_manifest(f"{manifest['metadata']['name']}-{manifest['kind']}", manifest)
        