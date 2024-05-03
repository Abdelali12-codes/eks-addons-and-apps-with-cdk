from aws_cdk import (
    # Duration,
    Stack,
    CfnOutput
    # aws_sqs as sqs,
)
import aws_cdk.aws_eks as eks
from constructs import Construct
from aws_cdk.lambda_layer_kubectl_v27 import KubectlV27Layer
from .policies.main import *
from .resources import *
from .addons  import EksAuth, AlbIngress, FargateProfile, ExternalSecret, ArgocdApp
from .applications.main import Applications
from .resources.custom_resources_cdk.essecret.create_es_secret import CreateEsSecret

class EksPythonStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

       

        vpc = Vpc(self,construct_id)
        master_role = eks_master_role(self)
        node_role = eks_node_role(self)
        

        # eks cluster 
        cluster = eks.Cluster(self, "ekscluster", 
              cluster_name="eks-cluster",
              vpc=vpc.vpc,
              vpc_subnets=[ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)],
              version=eks.KubernetesVersion.V1_29,
              role=master_role,
              default_capacity=0,
              kubectl_layer=KubectlV27Layer(self, "layer")
            )
        
       
        # # Fargate Profile
        eksprofile = FargateProfile(self, "fargateprofiles", 
                       cluster=cluster, 
                       vpc=vpc.vpc, 
                       namespaces=["microservices","default","kube-system", "external-secret", "argocd"]
                    )
        
        # EksAuth
        EksAuth(self, 'eksauth', cluster=cluster, node_role=node_role)

        # # cloudfront
        Cloudfront(self,"cloudfronts3")
        

        # Argocd App
        #argocd = ArgocdApp(self, "argocdapp", cluster=cluster)

        # # rds instance
        db = RdsDatabase(self, "rdsinstance", vpc = vpc.vpc)

        # # es 
        essecret = CreateEsSecret(self, "EsScret", username=opensearch['es_username'], secretname=opensearch["secretname"])
        es = Opensearch(self, "opensearchinstance", vpc = vpc)
        es.node.add_dependency(essecret)

        # # # dynamodb
        # DynamodbTable(self,"apptables")
        
        # # # api gateway and socket
        # ApiGateway(self, 'apigateways')
        
        # external secret
        externalsecret = ExternalSecret(self, "externalsecret", cluster=cluster)
        #externalsecret.node.add_dependency(essecret)

        # # ALB Ingress
        ingress = AlbIngress(self, "eksalbingress", cluster=cluster, vpc=vpc.vpc)
        
        # # # Deploy Apps 
        # Applications(self, "applications", 
        #              externalsecret=externalsecret, 
        #              db_secret= db.dbsecret,
        #              db_host=db.rds_endpoint,
        #              es_domain=es.domain_endpoint,
        #              cognito_domain="cognito.domain_name",
        #              cluster= cluster,
        #              vpc = vpc,
        #              ingress = ingress,
        #              eksprofile=eksprofile
        #             )
        
