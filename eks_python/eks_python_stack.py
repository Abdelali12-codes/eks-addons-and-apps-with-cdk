from aws_cdk import (
    # Duration,
    Stack,
    CfnOutput
    # aws_sqs as sqs,
)
from constructs import Construct
from aws_cdk.lambda_layer_kubectl_v27 import KubectlV27Layer
from .policies.main import *
from .resources import *
from .application import  *
from .resources.custom_resources_cdk.esmappings import *
from .addons  import (
    EksAuth, 
    Keda, 
    Dashboard, 
    Opentelemetry, 
    CertManagerAddon, 
    IngressNginx, 
    ExternalDns, 
    EbsDriver, 
    EfsDriver,
    ExternalSecret
)
from  .configuration.config import opensearch

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
            desired_size=2,
            max_size=4,
            node_role= node_role,
            subnets= ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC),
            instance_types= [ec2.InstanceType.of(ec2.InstanceClass.M6G, ec2.InstanceSize.XLARGE)]
        )
        # client Vpn
        # ClientVpn(self, "clientVpn", vpc_instance=vpc.vpc)
        
        # EksAuth
        EksAuth(self, 'eksauth', cluster=cluster, node_role=node_role)
        
        # efs driver 
        efsdriver = EfsDriver(self, "efsdriver", cluster=cluster)
        # ebs driver 
        ebsdriver = EbsDriver(self, "ebsdriver", cluster=cluster)

        # rds 
        rdsdb = RdsDatabase(self, "rdsdb", vpc=vpc.vpc)

        # Airflow
        airflow = Airflow(self, 'Airflow', cluster=cluster, secret= rdsdb.dbsecret)
        # Keda
        # Keda(self, 'keda', cluster=cluster)

        # Dashboard
        # Dashboard(self, 'dashboard', cluster=cluster)

        # Opensearch
        #opensearch = Opensearch(self, "Opensearch", cluster=cluster, vpc=vpc)

        # FluentBit
        #fluentbit = FluentBit(self, 'flutterbit', cluster=cluster,
        #          esdomain=opensearch.cfn_domain.attr_domain_endpoint,
        #          esdomainname=opensearch.cfn_domain.domain_name)

        # Create ES Role Mapping
        #esmapping = EsMapping(self,"esmapping", esdomaine=opensearch.domain_endpoint,
        #          secretname=opensearch.essecret.secret_name,
        #          fluentbitrolearn=fluentbit.fluentbitrole.role_arn
        #          )

        # cert manager
        certmanger = CertManagerAddon(self, "certmanager", cluster=cluster, noderole=node_role)

        # ingress nginx
        IngressNginx(self, "ingressnginx", cluster=cluster)

        # opentelemetry
        # otel = Opentelemetry(self, 'opentelemetry', cluster=cluster)
        # otel.node.add_dependency(certmanger)

        # karpenter
        #EksKarpenter(self, "ekskarpenter", cluster=cluster, namespace="karpenter")

        # # keycloak secret 
        # keycloaksecret = KeycloakSecret(self, "keycloak")

        # # s3 driver
        # S3DriverMount(self, "s3driver", cluster=cluster)

        # # argocd
        # # ArgocdApp(self, "argocdapp", cluster=cluster)

        # external dns
        ExternalDns(self, "externaldns", cluster=cluster)
        
        # external secret
        externalsecret = ExternalSecret(self, "externalsecret", cluster=cluster)

        # # Applications
        # keycloakapp = KeycloakApp(self, "keycloakapp", cluster=cluster, dbsecret= rdsdb, 
        #             keycloaksecret=keycloaksecret, ssmdata= rdsdb.ssmdata)
        
        # keycloakapp.node.add_dependency(externalsecret)
        # applications = Applications(self, "k8sapplications", cluster=cluster, noderole=node_role, db=rdsdb)
        # applications.node.add_dependency(certmanger)
        # applications.node.add_dependency(externalsecret)
        airflow.node.add_dependency(ebsdriver)
        airflow.node.add_dependency(efsdriver)
        airflow.node.add_dependency(certmanger)
        airflow.node.add_dependency(externalsecret)

        