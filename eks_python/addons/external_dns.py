from aws_cdk import (Resource, RemovalPolicy)
from jinja2 import Environment, FileSystemLoader
import os 
import yaml
from cdk_ecr_deployment import DockerImageName, ECRDeployment
from ..policies.main import ExternalDnsRole

DIR = os.path.dirname(os.path.realpath(__file__))

class ExternalDns(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)

        cluster = None 

        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide cluster arg")
        
        
        env = Environment(loader=FileSystemLoader(DIR))

        template = env.get_template('external-dns.yaml.j2')

        role = ExternalDnsRole(self, cluster)

        rendered_template = template.render({
            'domain': "abdelalitraining.com",
            'hostedzoneid': "Z05045244G4M5OFGHB4C",
            'role_arn': role.role_arn,
        })
        
        yaml_file = yaml.safe_load_all(rendered_template)

        for i, manifest in enumerate(yaml_file):
             cluster.add_manifest(f'externadns-{manifest['kind'].lower()}', manifest)