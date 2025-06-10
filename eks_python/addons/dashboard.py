from aws_cdk import (Resource, Stack, RemovalPolicy)
import aws_cdk.aws_eks as eks


class Dashboard(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)

        cluster = None
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")

        dashboard = eks.HelmChart(self, "dashboardhelm",
                             cluster=cluster,
                             namespace="kubernetes-dashboard",
                             create_namespace=True,
                             repository="https://kubernetes.github.io/dashboard/",
                             chart="kubernetes-dashboard",
                             release="kubernetes-dashboard",
                             wait=False
                             )


