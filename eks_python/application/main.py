from aws_cdk import (Resource, CfnDynamicReference,Fn, Stack, CfnDynamicReferenceService)
from jinja2 import Environment, FileSystemLoader
from ..policies.main import CertManagerRole
import os
import json
import glob
import yaml
from ..configuration.config import *

DIR = os.path.dirname(os.path.realpath(__file__))


class Applications(Resource):
    def __init__(self, scope, id,  cluster, noderole, db,**kwargs):
        super().__init__(scope, id)
        count = 0

        certmanager = CertManagerRole(self, cluster, noderole)
        for item in glob.glob(os.path.join(DIR, '*.yaml')):
            file = os.path.basename(item)
            with open(os.path.join(DIR, file)) as content:
                documents = yaml.load_all(content)

                for index, manifest in enumerate(documents):
                    
                    if 'deployment' in manifest['kind'].lower():
                        manifest['spec']['template']['spec']['containers'][0]['envFrom'] = [
                            {
                                "secretRef": {
                                    "name": f"{manifest['metadata']['name']}-sm",
                                }
                            },
                             {
                                "secretRef": {
                                    "name": f"{manifest['metadata']['name']}-ssm",
                                }
                            }
                        ]

                        # secretmanager secret
                        cluster.add_manifest(f'{manifest['metadata']['name']}-externalsecret-sm',{
                                "apiVersion": "external-secrets.io/v1beta1",
                                "kind": "ExternalSecret",
                                "metadata":{
                                    "name": f"{manifest['metadata']['name']}-sm",
                                    "namespace": manifest['metadata']['namespace']
                                },
                                "spec":{
                                    "refreshInterval": "1h",
                                    "secretStoreRef": {
                                        "name": "aws-secrets-manager",
                                        "kind": "ClusterSecretStore"
                                    },
                                    "target":{
                                        "name": f"{manifest['metadata']['name']}-sm",
                                        "creationPolicy": "Owner"
                                    },
                                    ## You can get all of the secret content (recommended)
                                    # "dataFrom":[
                                    #     {
                                    #         "extract":{
                                    #             "key": "secretname"
                                    #         }
                                    #     }
                                    # ],
                                    "data": [                            
                                    {
                                        "secretKey": "DB_USERNAME",
                                        "remoteRef": {
                                            "key": rdsdb['secretname'],
                                            "property": "username"
                                        }
                                    },
                                    {
                                        "secretKey": "DB_PASSWORD",
                                        "remoteRef": {
                                            "key": rdsdb['secretname'],
                                            "property": "password"
                                        }
                                    }
                                    ]
            
                                }
                        })

                        # ssm secret

                        cluster.add_manifest(f'{manifest['metadata']['name']}-externalsecret-ssm',{
                                "apiVersion": "external-secrets.io/v1beta1",
                                "kind": "ExternalSecret",
                                "metadata":{
                                    "name": f"{manifest['metadata']['name']}-ssm",
                                    "namespace": manifest['metadata']['namespace']
                                },
                                "spec":{
                                    "refreshInterval": "1h",
                                    "secretStoreRef": {
                                        "name": "aws-parameter-store",
                                        "kind": "ClusterSecretStore"
                                    },
                                    "target":{
                                        "name": f"{manifest['metadata']['name']}-ssm",
                                        "creationPolicy": "Owner"
                                    },
                                    "data": [                            
                                    {
                                        "secretKey": "DB_HOST",
                                        "remoteRef": {
                                            "key": "/db/endpoint"
                                        }
                                    },
                                    {
                                        "secretKey": "DB_DATABASE",
                                        "remoteRef": {
                                            "key": "/db/dbname"
                                        }
                                    }
                                    ]
            
                                }
                        })
                    cluster.add_manifest(f'{manifest['metadata']['name']}-{manifest['kind']}', manifest)
                
                # deploy ingress for application
                
                env = Environment(loader=FileSystemLoader(DIR))
                template = env.get_template('cluster_issuer.yaml.j2')
                rendered_template = template.render({
                    "email": clusterissuer['email'],
                    "hostedZoneName": clusterissuer['hostedZoneName'],
                    "hostedZoneID": clusterissuer['hostedZoneID'],
                    "rolearn": certmanager.role_arn
                })

                manifest = yaml.safe_load(rendered_template)
                cluster.add_manifest('cluster-issuer', manifest)

                

        
        
