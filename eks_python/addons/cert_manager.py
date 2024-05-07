from aws_cdk import (Resource)
import aws_cdk.aws_eks as eks
from ..policies.main import ExternalDnsRole

class CertManagerAddon(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)
        

        cluster = None 
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")
        
        #externaldnsiamrole = ExternalDnsRole(self, cluster=cluster)

        eks.HelmChart(self, "certchart",
                      cluster= cluster,
                      namespace= "cert-manager",
                      release="cert-manager",
                      create_namespace=True,
                      repository="https://charts.jetstack.io",
                      wait=False,
                      chart="cert-manager",
                      values= {
                          "installCRDs": "true",
                          "serviceAccount":{
                              "name": "cert-manager",
                            #   "annotations": {
                            #       "eks.amazonaws.com/role-arn": externaldnsiamrole.role_arn
                            #   }
                          }
                      }
                    )
        
       