from aws_cdk import (Resource)
import aws_cdk.aws_eks as eks
from ..configuration.config import *


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
                          "global":{
                              "domain": argocd['hostname']
                          },
                          "server": {
                           "ingress":{
                               "enabled": "true",
                               "ingressClassName": "ingress-nginx",
                               "annotations": {
                                   "cert-manager.io/cluster-issuer": "dns-01-production",
                                   "nginx.ingress.kubernetes.io/backend-protocol": "HTTPS"
                               },
                               "tls": "true",
                               "hostname": argocd['hostname']
                            }
                          },
                          "configs":{
                              "cm":{
                                  "dex.config": f"connectors:\n- type: gitlab\n  id: gitlab\n  name: GitLab\n  config:\n    baseURL: https://gitlab.com\n    clientID: {gitlabapplication['clientid']}\n    clientSecret: {gitlabapplication['clientsecret']}\n    redirectURI: http://argocd-dex-server:5556/dex/callback"
                                }
                              }
                          }
                      
                    )
        
       