from aws_cdk import (Resource, Stack)
from aws_cdk.aws_eks import AlbController, AlbControllerVersion
from ..configuration.config import REGION


class AlbIngress(Resource):
    def __init__(self, scope, id, **kawrgs):
        super().__init__(scope, id)
        cluster = None 

        if 'cluster'  in kawrgs:
            cluster = kawrgs['cluster']
        else:
            raise Exception('Please Provide the required Arguments by Resource')
        
        albingress = AlbController(self, "AlbController",
            cluster=cluster,
            version=AlbControllerVersion.V2_6_2,
            repository=f"602401143452.dkr.ecr.{Stack.of(self).region}.amazonaws.com/amazon/aws-load-balancer-controller"
        )
        
        ingressclass = cluster.add_manifest("ingressclass", {
                "apiVersion": "networking.k8s.io/v1",
                "kind": "IngressClass",
                "metadata": {
                    "name": "aws-ingress-class",
                    "annotations":{
                        "ingressclass.kubernetes.io/is-default-class": "true"
                    }
                },
                "spec":{
                    "controller": "ingress.k8s.aws/alb"
                }
        })

        ingressclass.node.add_dependency(albingress)
