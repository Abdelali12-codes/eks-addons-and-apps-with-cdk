from aws_cdk import (Resource, CfnDynamicReference,Fn, Stack, CfnDynamicReferenceService)
from jinja2 import Environment, FileSystemLoader
from ..policies.main import CertManagerRole
import os
import json
import glob
import yaml

DIR = os.path.dirname(os.path.realpath(__file__))


class Applications(Resource):
    def __init__(self, scope, id,  cluster, noderole,**kwargs):
        super().__init__(scope, id)
        count = 0

        certmanager = CertManagerRole(self, cluster, noderole)
        for item in glob.glob(os.path.join(DIR, '*.yaml')):
            file = os.path.basename(item)
            with open(os.path.join(DIR, file)) as content:
                documents = yaml.load_all(content)

                for index, manifest in enumerate(documents):
                  cluster.add_manifest(f'{manifest['metadata']['name']}-{manifest['kind']}', manifest)
                
                # deploy ingress for application
                
                env = Environment(loader=FileSystemLoader(DIR))
                template = env.get_template('cluster_issuer.yaml.j2')
                rendered_template = template.render({
                    "email": "jadelmoulaa2@gmail.com",
                    "hostedZoneName": "abdelalitraining.com",
                    "hostedZoneID": "Z05045244G4M5OFGHB4C",
                    "rolearn": certmanager.role_arn
                })

                manifest = yaml.safe_load(rendered_template)
                cluster.add_manifest('cluster-issuer', manifest)

                

        
        
