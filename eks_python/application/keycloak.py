from aws_cdk import (Resource, CfnDynamicReference,Fn, Stack, CfnDynamicReferenceService)
from jinja2 import Environment, FileSystemLoader
from ..policies.main import CertManagerRole
import os
import json
import glob
import yaml
from ..configuration.config import *

DIR = os.path.dirname(os.path.realpath(__file__))


class KeycloakApp(Resource):
    def __init__(self, scope, id,  cluster,dbsecret, keycloaksecret, ssmdata, **kwargs):
        super().__init__(scope, id)
        count = 0
        
        env = Environment(loader=FileSystemLoader(DIR))
        template = env.get_template('keycloak.yaml.j2')
        rendered_template = template.render({
            "keycloaksecret": keycloaksecret.keycloaksecret.secret_name,
            "rdssecret": dbsecret.dbsecret.secret_name,
            "dbendpointssm": ssmdata['endpoint'].parameter_name,
            "dbnamessm": ssmdata['dbname'].parameter_name
        })

        documents = yaml.load_all(rendered_template)    
        for index, manifest in enumerate(documents):
                cluster.add_manifest(f'{manifest['metadata']['name']}-{manifest['kind']}', manifest)
            
            