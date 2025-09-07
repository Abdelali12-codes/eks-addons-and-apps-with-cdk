from aws_cdk import (Resource)
import aws_cdk.aws_eks as eks
from jinja2 import Environment, FileSystemLoader
import yaml
import os
from ..configuration.config import *
from ..policies.main import CertManagerRole

DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

class CertManagerAddon(Resource):
    def __init__(self, scope, id , noderole, **kwargs):
        super().__init__(scope, id)
        

        cluster = None 
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")
        
        #externaldnsiamrole = ExternalDnsRole(self, cluster=cluster)

        chart = eks.HelmChart(self, "certchart",
                      cluster= cluster,
                      namespace= "cert-manager",
                      release="cert-manager",
                      create_namespace=True,
                      repository="https://charts.jetstack.io",
                      wait=False,
                      chart="cert-manager",
                      values= {
                          "installCRDs": True,
                          "serviceAccount":{
                              "name": "cert-manager",
                          }
                      }
                    )
        certmanager = CertManagerRole(self, cluster, noderole)
        env = Environment(loader=FileSystemLoader(os.path.join(DIR, 'application' )))
        template = env.get_template('cluster_issuer.yaml.j2')
        rendered_template = template.render({
            "email": clusterissuer['email'],
            "hostedZoneName": clusterissuer['hostedZoneName'],
            "hostedZoneID": clusterissuer['hostedZoneID'],
            "rolearn": certmanager.role_arn
        })

        manifest = yaml.safe_load(rendered_template)
        issuer = cluster.add_manifest('cluster-issuer', manifest)
        issuer.node.add_dependency(chart)
        
       