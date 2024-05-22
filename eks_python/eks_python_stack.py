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
from .application.keycloak import *
from .addons  import *


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
        # eks workernode
        cluster.add_nodegroup_capacity("eksnodegroupcapacity",
            min_size=1,
            desired_size=3,
            max_size=4,
            node_role= node_role,
            subnets= ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            instance_types= [ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM)]
        )

        # EksAuth
        EksAuth(self, 'eksauth', cluster=cluster, node_role=node_role)

        # keycloak secret 
        keycloaksecret = KeycloakSecret(self, "keycloak")

        # s3 driver
        S3DriverMount(self, "s3driver", cluster=cluster)

        # ebs driver 
        EbsDriver(self, "ebsdriver", cluster=cluster)

        # rds 
        rdsdb = RdsDatabase(self, "rdsdb", vpc=vpc.vpc)

        # argocd
        # ArgocdApp(self, "argocdapp", cluster=cluster)

        # ingress nginx
        IngressNginx(self, "ingressnginx", cluster=cluster)

        # cert manager
        certmanger = CertManagerAddon(self, "certmanager", cluster=cluster , noderole=node_role)

        # external dns
        ExternalDns(self, "externaldns", cluster=cluster)
        
        # external secret
        externalsecret = ExternalSecret(self, "externalsecret", cluster=cluster)

        # Applications
        keycloakapp = KeycloakApp(self, "keycloakapp", cluster=cluster, dbsecret= rdsdb, 
                    keycloaksecret=keycloaksecret, ssmdata= rdsdb.ssmdata)
        
        keycloakapp.node.add_dependency(externalsecret)
        # applications = Applications(self, "k8sapplications", cluster=cluster, noderole=node_role, db=rdsdb)
        # applications.node.add_dependency(certmanger)
        # applications.node.add_dependency(externalsecret)

        