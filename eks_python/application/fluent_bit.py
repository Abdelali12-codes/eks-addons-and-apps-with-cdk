from aws_cdk import (Resource, CfnDynamicReference, Fn, Stack, CfnDynamicReferenceService)
from jinja2 import Environment, FileSystemLoader
import aws_cdk.aws_eks  as eks
from ..policies.main import FluentBitSaRole
import os
import json
import glob
import yaml
from ..configuration.config import *

DIR = os.path.dirname(os.path.realpath(__file__))


class FluentBit(Resource):
    def __init__(self, scope, id, cluster: eks.ICluster, esdomainname, esdomain, **kwargs):
        super().__init__(scope, id)

        self.fluentbitrole = FluentBitSaRole(self, cluster, "logging", "fluent-bit", esdomainname)
        fluentbit_namespace = eks.KubernetesManifest(
            self,
            "fluent-bit-namespace",
            cluster=cluster,
            manifest=[{
                "apiVersion": "v1",
                "kind": "Namespace",
                "metadata": {"name": "logging"}
            }]
        )
        env = Environment(loader=FileSystemLoader(DIR))
        template = env.get_template('fluent_bit.yaml.j2')
        rendered_template = template.render({
            "esdomain": esdomain,
            "awsregion": Stack.of(self).region,
            "namespace": "logging",
            "role_arn": self.fluentbitrole.role_arn
        })

        documents = yaml.load_all(rendered_template)
        for index, manifest in enumerate(documents):
            manifest = cluster.add_manifest(f'{manifest['metadata']['name']}-{manifest['kind']}', manifest)
            manifest.node.add_dependency(fluentbit_namespace)
