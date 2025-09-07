from aws_cdk import (Resource, Stack, CfnOutput, RemovalPolicy)
import aws_cdk.aws_eks as eks
import  aws_cdk.aws_aps as aps
import  aws_cdk.aws_logs as logs
from jinja2 import Environment, FileSystemLoader
import  os
import  yaml
from ..policies.main import AdotServiceAccount

DIR = os.path.dirname(os.path.realpath(__file__))

class Opentelemetry(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)

        cluster = None
        resources_dependency = {}
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")

        adotrole = AdotServiceAccount(self, cluster, 'aws-otel-eks', 'aws-otel-collector')

        loggroup = logs.LogGroup(self, "apslogrgoup", log_group_name="/aps/opentelemetry",
                                 removal_policy=RemovalPolicy.DESTROY
                                 )
        managedprometheus = aps.CfnWorkspace(self, 'managedprometheus',
                      alias= "otel",
                      logging_configuration= aps.CfnWorkspace.LoggingConfigurationProperty(
                          log_group_arn=loggroup.log_group_arn
                      )
                    )
        adotaddon = eks.CfnAddon(self, 'adotaddon',
                      addon_name='adot',
                      cluster_name= cluster.cluster_name,
                      addon_version= "v0.117.0-eksbuild.1"
                    )

        env = Environment(loader=FileSystemLoader(DIR))

        template = env.get_template('otel-collector-xray-prometheus.yaml.j2')

        rendered_template = template.render({
             "ENDPOINT": managedprometheus.attr_prometheus_endpoint + "api/v1/remote_write",
             "REGION": Stack.of(self).region,
             "APPLICATIONS": "flask-prometheus-service:5000"
        })

        yaml_file = yaml.safe_load_all(rendered_template)

        for i, manifest in enumerate(yaml_file):
            k8s_manifest = cluster.add_manifest(f'opentelemetry-{manifest['kind'].lower()}', manifest)
            k8s_manifest.node.add_dependency(adotaddon)
            resources_dependency[f'opentelemetry-{manifest['kind'].lower()}'] = k8s_manifest

        CfnOutput(self, "aps", value=managedprometheus.attr_prometheus_endpoint)