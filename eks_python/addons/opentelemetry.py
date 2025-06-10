from aws_cdk import (Resource, Stack, RemovalPolicy)
import aws_cdk.aws_eks as eks
import  aws_cdk.aws_aps as aps
import  aws_cdk.aws_logs as logs
from ..policies.main import AdotServiceAccount

class Opentelemetry(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)

        cluster = None
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")
        adotrole = AdotServiceAccount(self, cluster, 'opentelemetry', 'adot-collector')

        loggroup = logs.LogGroup(self, "apslogrgoup", log_group_name="/aps/opentelemetry",
                                 removal_policy=RemovalPolicy.DESTROY
                                 )
        managedprometheus = aps.CfnWorkspace(self, 'managedprometheus',
                      logging_configuration= aps.CfnWorkspace.LoggingConfigurationProperty(
                          log_group_arn=loggroup.log_group_arn
                      )
                    )
        opentelemetrycollector = eks.HelmChart(self, "adothelm",
                                 cluster=cluster,
                                 namespace="opentelemetry",
                                 repository="https://open-telemetry.github.io/opentelemetry-helm-charts",
                                 chart="opentelemetry-kube-stack",
                                 release="opentelemetry-kube-stack",
                                 wait=False,
                                 values= {
                                     "mode": "deployment",
                                     "image": {
                                       "repository": "otel/opentelemetry-collector-k8s",
                                       "tag": "0.126.0"
                                     },
                                     "extraEnvs": [
                                         {
                                             "name": "AWS_REGION",
                                             "value": Stack.of(self).region
                                         },
                                         {
                                             "name": "AWS_PROMETHEUS_ENDPOINT",
                                             "value": managedprometheus.attr_prometheus_endpoint
                                         }
                                     ],
                                     "serviceAccount": {
                                         "create": False,
                                         "name": "adot-collector"
                                     },
                                     "config": {
                                         "extensions": {
                                             "health_check": {},
                                             "sigv4auth": {
                                                 "region": "'$AWS_REGION'",
                                                 "service": "aps"
                                             }
                                         },
                                         "receivers": {
                                             "prometheus": {
                                                 "config": {
                                                    "global": {
                                                      "scrape_interval": "15s",
                                                      "scrape_timeout": "10s"
                                                    },
                                                    "scrape_configs": [
                                                        {
                                                            "job_name": "prometheus",
                                                            "static_configs" : [
                                                                {
                                                                    "targets": ["'$AWS_PROMETHEUS_SCRAPING_ENDPOINT'"]
                                                                }
                                                            ]
                                                        }
                                                    ]
                                                 }
                                             },
                                             "awsxray": {
                                                 "endpoint": "0.0.0.0:2000",
                                                 "transport": "udp"
                                             }
                                         },
                                         "processors": {
                                               "batch/metrics": {
                                                   "timeout": "60s"
                                               }
                                         },
                                         "exporters": {
                                             "prometheusremotewrite": {
                                                 "endpoint": "'$AWS_PROMETHEUS_ENDPOINT'",
                                                 "auth": {
                                                     "authenticator": "sigv4auth"
                                                 }
                                             },
                                             "logging": {
                                                 "loglevel": "info"
                                             },
                                             "awsxray": {}
                                         },
                                         "service": {
                                             "pipelines": {
                                                 "metrics": {
                                                     "receivers": ["prometheus"],
                                                     "processors": ["batch / metrics"],
                                                     "exporters": [ "prometheusremotewrite", "logging"]
                                                 }
                                             },
                                             "extensions": ["health_check", "sigv4auth"]
                                         }
                                     }
                                 }
                             )


