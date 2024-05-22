from aws_cdk import (Resource)
import aws_cdk.aws_eks as eks
from ..configuration.config import *
from ..policies.main import *
from jinja2 import Environment, FileSystemLoader
import os 

DIR = os.path.dirname(os.path.realpath(__file__))

class S3DriverMount(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)

        cluster = None 
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")
    
        S3DriverMountServicea(self, cluster=cluster)
        argohelm = eks.HelmChart(self, "s3drivermount",
                      cluster= cluster,
                      namespace= "kube-system",
                      repository="https://awslabs.github.io/mountpoint-s3-csi-driver",
                      release="aws-mountpoint-s3-csi-driver",
                      wait=True,
                      chart="aws-mountpoint-s3-csi-driver",
                      values= {
                          "node": {
                              "serviceAccount": {
                                  "create": "false",
                                  "name": "s3-csi-driver-sa"
                              }
                          }
                      }
                      
                    )
        
       