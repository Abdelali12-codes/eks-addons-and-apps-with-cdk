from aws_cdk import (Stack,Resource, RemovalPolicy, CfnOutput, CfnDynamicReference, CfnDynamicReferenceService)
import aws_cdk.aws_opensearchservice as es
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_secretsmanager as secret
import aws_cdk.aws_iam as iam
from .custom_resources_cdk.essecret.create_es_secret import CreateEsSecret
from ..configuration.config import opensearch



class Opensearch(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)
        
        vpc = None 

        if 'vpc' in kwargs:
           vpc = kwargs['vpc']
        else:
            raise Exception('Please Provide the Vpc Arg')

        es_sg = ec2.SecurityGroup(self, "ESSecurityGroup",
            vpc=vpc.vpc,
            description="es-sg",
            security_group_name="es-sg",
            allow_all_outbound=True,
        )

        es_sg.add_ingress_rule(ec2.Peer.ipv4(vpc.vpc.vpc_cidr_block), ec2.Port.tcp(443), "allow https")
        es_sg.add_ingress_rule(ec2.Peer.ipv4(vpc.vpc.vpc_cidr_block), ec2.Port.tcp(80), "allow http")
        

       
        cfn_domain = es.CfnDomain(self, "MyCfnDomain",
            advanced_security_options=es.CfnDomain.AdvancedSecurityOptionsInputProperty(
                anonymous_auth_disable_date="anonymousAuthDisableDate",
                anonymous_auth_enabled=False,
                enabled=True,
                internal_user_database_enabled=True,
                master_user_options=es.CfnDomain.MasterUserOptionsProperty(
                    master_user_name=CfnDynamicReference(CfnDynamicReferenceService.SECRETS_MANAGER, 
                                                    f"{opensearch["secretname"]}:SecretString:username").to_string(),
                    master_user_password=CfnDynamicReference(CfnDynamicReferenceService.SECRETS_MANAGER, 
                                                    f"{opensearch["secretname"]}:SecretString:password").to_string()
                )
            ),
            domain_endpoint_options=es.CfnDomain.DomainEndpointOptionsProperty(
                enforce_https=True,
            ),
            cluster_config=es.CfnDomain.ClusterConfigProperty(
                cold_storage_options=es.CfnDomain.ColdStorageOptionsProperty(
                    enabled=False
                ),
                # dedicated_master_count=1,
                dedicated_master_enabled=False,
                instance_count=opensearch["capacity"]["data_nodes"],
                instance_type=opensearch["capacity"]["data_node_instance_type"],
                multi_az_with_standby_enabled=False,
                # zone_awareness_config=es.CfnDomain.ZoneAwarenessConfigProperty(
                #     availability_zone_count=
                # ),
                # zone_awareness_enabled=False
            ),
            domain_name=opensearch["es_domain_name"],
            ebs_options=opensearch["ebs"],
            encryption_at_rest_options=es.CfnDomain.EncryptionAtRestOptionsProperty(
                enabled=True,
            ),
            engine_version=opensearch["version"],
            node_to_node_encryption_options=es.CfnDomain.NodeToNodeEncryptionOptionsProperty(
                enabled=True
            ),
            vpc_options=es.CfnDomain.VPCOptionsProperty(
                security_group_ids=[es_sg.security_group_id],
                subnet_ids=[vpc.private_subnets[0]]
            ),
            
        )

        self.domain_endpoint = cfn_domain.attr_domain_endpoint

       

        cfn_domain.apply_removal_policy(policy=RemovalPolicy.DESTROY)

        CfnOutput(self, "opensearchdomain", value=cfn_domain.attr_domain_endpoint)


        