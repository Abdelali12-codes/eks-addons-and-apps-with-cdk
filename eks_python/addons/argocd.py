from aws_cdk import (Resource)
import aws_cdk.aws_eks as eks


class ArgocdApp(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)
        
        cluster = None 
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")
        

        
        eks.HelmChart(self, "argocdchart",
                      cluster= cluster,
                      namespace= "argocd",
                      repository="https://argoproj.github.io/argo-helm",
                      release="argocd",
                      wait=False,
                      chart="argo-cd",
                      values= {
                          "server": {
                           "service": {
                               "type": "LoadBalancer"
                           }   
                          }
                      }
                    )
        
       