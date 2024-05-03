from aws_cdk import (Resource)
import aws_cdk.aws_eks as eks


class CertManagerAddon(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)
        
        cluster = None 
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")
        
        eks.HelmChart(self, "nginxingress",
                      cluster= cluster,
                      namespace= "ingress-nginx",
                      release="ingress-nginx",
                      create_namespace=True,
                      repository="https://kubernetes.github.io/ingress-nginx",
                      wait=False,
                      chart="ingress-nginx",
                      values= {
                          "service":{
                              "annotations": {
                                    "service.beta.kubernetes.io/aws-load-balancer-type": "nlb"
                              }
                          }
                      }
                    )
        
       