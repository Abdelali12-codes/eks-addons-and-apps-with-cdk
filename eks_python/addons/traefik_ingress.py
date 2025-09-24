from aws_cdk import (Resource)
import aws_cdk.aws_eks as eks


class TraefikIngress(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)
        
        cluster = None 
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")
        
        eks.HelmChart(self, "traefikingress",
                      cluster= cluster,
                      namespace= "traefik",
                      release="traefik",
                      create_namespace=True,
                      repository="https://helm.traefik.io/traefik",
                      wait=False,
                      chart="traefik",
                      values= {
                          "ingressClass": {
                            "enabled": True,
                            "isDefaultClass": True,
                            "fallbackApiVersion": "v1" 
                          },
                          "ingressRoute": {
                            "dashboard": {
                               "enabled": True
                            }
                          },
                          "service": {
                            "annotations": {
                               "service.beta.kubernetes.io/aws-load-balancer-type": "nlb"
                            }
                          },
                          "globalArguments": [
                              "--api.insecure=true"
                          ]
                      }
                    )
        
       