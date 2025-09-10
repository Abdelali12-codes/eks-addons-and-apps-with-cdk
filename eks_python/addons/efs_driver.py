from aws_cdk import (Resource)
import aws_cdk.aws_eks as eks
from ..configuration.config import *
from ..policies.main import *
from jinja2 import Environment, FileSystemLoader
import os 

DIR = os.path.dirname(os.path.realpath(__file__))

class EfsDriver(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)

        cluster = None 
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")
    
        EfsDriverServicea(self, cluster=cluster)
        argohelm = eks.HelmChart(self, "efs-csi-helm-chart",
                      cluster= cluster,
                      namespace= "kube-system",
                      repository="https://kubernetes-sigs.github.io/aws-efs-csi-driver",
                      release="aws-efs-csi-driver",
                      wait=True,
                      chart="aws-efs-csi-driver",
                      values= {
                           "controller": {
                            "serviceAccount": {
                                "create": False,
                                "name": "efs-csi-controller-sa",
                            }
                            },
                      }
                      
                    )
        
       