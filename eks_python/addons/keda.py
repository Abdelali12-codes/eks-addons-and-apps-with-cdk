from aws_cdk import (Resource, Stack, RemovalPolicy)
import aws_cdk.aws_eks as eks


class Keda(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)

        cluster = None
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")

        keda = eks.HelmChart(self, "kedahelm",
                                       cluster=cluster,
                                       namespace="keda",
                                       create_namespace=True,
                                       repository="https://kedacore.github.io/charts",
                                       chart="keda",
                                       release="keda",
                                       wait=False,
                                       version="2.13.1"
                                       )

        
