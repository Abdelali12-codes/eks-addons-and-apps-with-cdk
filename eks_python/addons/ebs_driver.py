from aws_cdk import (Resource)
import aws_cdk.aws_eks as eks
from ..configuration.config import *
from ..policies.main import *
from jinja2 import Environment, FileSystemLoader
import os 

DIR = os.path.dirname(os.path.realpath(__file__))

class EbsDriver(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)

        cluster = None 
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")
    
        EbsDriverServicea(self, cluster=cluster)
        argohelm = eks.HelmChart(self, "ebs-csi-helm-chart",
                      cluster= cluster,
                      namespace= "kube-system",
                      repository="https://kubernetes-sigs.github.io/aws-ebs-csi-driver",
                      release="aws-ebs-csi-driver",
                      wait=True,
                      chart="aws-ebs-csi-driver",
                      values= {
                           "controller": {
                            "serviceAccount": {
                                "create": "false",
                                "name": "ebs-csi-controller-sa",
                            }
                            },
                      }
                      
                    )
        
       