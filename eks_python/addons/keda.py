from aws_cdk import (Resource, Stack, RemovalPolicy)
import aws_cdk.aws_eks as eks
from jinja2 import Environment, FileSystemLoader
import os
import  yaml
from ..policies.main import KedaServiceAccount

DIR = os.path.dirname(os.path.realpath(__file__))

class Keda(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)

        cluster = None
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")

        kedasa = KedaServiceAccount(self, cluster, 'keda', 'keda-operator' )
        keda = eks.HelmChart(self, "kedahelm",
                                       cluster=cluster,
                                       namespace="keda",
                                       create_namespace=True,
                                       repository="https://kedacore.github.io/charts",
                                       chart="keda",
                                       release="keda",
                                       wait=False,
                                       version="2.13.1",
                                       values={
                                           "operator": {
                                               "name": "keda-operator"
                                           },
                                           "podSecurityContext": {
                                               "fsGroup": 1001
                                           },
                                           "securityContext": {
                                               "runAsGroup": 1001,
                                               "runAsUser": 1001
                                           },
                                           "serviceaccount": {
                                               "create": False,
                                               "name": "keda-operator"
                                           }
                                       }
                                       )

        keda.node.add_dependency(kedasa)

        env = Environment(loader=FileSystemLoader(DIR))

        template = env.get_template('keda-proxy.yaml.j2')

        rendered_template = template.render({
            "REGION": Stack.of(self).region,
        })

        yaml_file = yaml.safe_load_all(rendered_template)

        for i, manifest in enumerate(yaml_file):
            k8s_manifest = cluster.add_manifest(f'keda-{manifest['kind'].lower()}', manifest)
            k8s_manifest.node.add_dependency(kedasa)