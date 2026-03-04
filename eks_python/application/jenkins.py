from aws_cdk import (Resource, RemovalPolicy, CfnDynamicReference, Fn, Stack, CfnDynamicReferenceService)
from jinja2 import Environment, FileSystemLoader
import aws_cdk.aws_eks  as eks
import aws_cdk.aws_efs as efs
import yaml
import textwrap
import os
from ..configuration.config import *

DIR = os.path.dirname(os.path.realpath(__file__))


class Jenkins(Resource):
    def __init__(self, scope, id, cluster: eks.ICluster, vpc, **kwargs):
        super().__init__(scope, id)
        jenkinsnamespace = eks.KubernetesManifest(
                self,
                "jenkinsnamespace",
                cluster=cluster,
                manifest=[{
                       "apiVersion": "v1",
                       "kind": "Namespace",
                       "metadata": {"name": "jenkins"}
                }]
            )
                    
        jenkinshelm = eks.HelmChart(self, "jenkins-helm-chart",
                      cluster= cluster,
                      namespace= "jenkins",
                      create_namespace=False,
                      repository="https://kubernetes-charts.storage.googleapis.com/",
                      release="jenkins",
                      wait=False,
                      chart="jenkins",
                      values= {
                          "rbac":{
                            "create": True
                          },
                          "master": {
                              "servicePort": 80
                          },
                          "persistence": {
                              "existingClaim": "efs-claim"
                          }
                      }
                      
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
        
        efs_sg = ec2.SecurityGroup(self, "SecurityGroup",
            vpc=vpc,
            description="efs-sg",
            security_group_name="efs-sg",
            allow_all_outbound=True,
        )
        efs_sg.add_ingress_rule(ec2.Peer.ipv4(vpc.vpc_cidr_block), ec2.Port.tcp(2049), "allow postgres")
        
        file_system = efs.FileSystem(self, "EfsFileSystem",
            vpc=vpc,
            security_group= efs_sg,
            file_system_name= "jenkins",
            vpc_subnets= ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            )
        )
        
        efs_access_point = efs.AccessPoint(self, "efsaccesspoint", 
                file_system= file_system,
                path= "/jenkins",
                create_acl=efs.Acl(
                    owner_uid="1000",
                    owner_gid="1000",
                    permissions="777"
                ),
                posix_user=efs.PosixUser(
                    uid="1000",
                    gid="1000"
                )                             
            )
        env = Environment(loader=FileSystemLoader(DIR))
        template = env.get_template('jenkins_pvc.yaml.j2')
        rendered_template = template.render({
            "efs_access_point": efs_access_point.access_point_id
        })

        documents = yaml.load_all(rendered_template)    
        for index, manifest in enumerate(documents):
                cluster.add_manifest(f"{manifest['metadata']['name']}-{manifest['kind']}", manifest)
        