from aws_cdk import (Stack, Resource, RemovalPolicy, CfnOutput, CfnDynamicReference, CfnDynamicReferenceService)
import aws_cdk.aws_opensearchservice as es
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_secretsmanager as secret
import  aws_cdk.aws_iam as iam
import json
from ..configuration.config import opensearch


class Opensearch(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)
        vpc = None
        if 'vpc' in kwargs:
            vpc = kwargs['vpc']
        else:
            raise Exception('Please Provide the Vpc Arg')

        self.essecret = secret.Secret(self, "opensearch-creds",
                                      secret_name="opensearch-creds",
                                      generate_secret_string=secret.SecretStringGenerator(
                                          secret_string_template=json.dumps({"username": "appuser"}),
                                          exclude_punctuation=False,
                                          password_length=16,
                                          generate_string_key="password"
                                      )
                                      )

        es_sg = ec2.SecurityGroup(self, "ESSecurityGroup",
                                  vpc=vpc.vpc,
                                  description="es-sg",
                                  security_group_name="es-sg",
                                  allow_all_outbound=True,
                                  )

        es_sg.add_ingress_rule(ec2.Peer.ipv4('0.0.0.0/0'), ec2.Port.tcp(443), "allow https")
        es_sg.add_ingress_rule(ec2.Peer.ipv4('0.0.0.0/0'), ec2.Port.tcp(80), "allow http")

        self.cfn_domain = es.CfnDomain(self, "CfnOpenSearchDomain",
                                  access_policies= iam.PolicyDocument(statements=[
                                      iam.PolicyStatement(
                                          actions=["es:ESHttp*"],
                                          effect=iam.Effect.ALLOW,
                                          principals=[iam.AnyPrincipal()],
                                          resources=[
                                              f"arn:{Stack.of(self).partition}:es:{Stack.of(self).region}:{Stack.of(self).account}:domain/{opensearch['es_domain_name']}/*"]
                                      )
                                  ]),
                                  advanced_security_options=es.CfnDomain.AdvancedSecurityOptionsInputProperty(
                                      anonymous_auth_disable_date="anonymousAuthDisableDate",
                                      anonymous_auth_enabled=False,
                                      enabled=True,
                                      internal_user_database_enabled=True,
                                      master_user_options=es.CfnDomain.MasterUserOptionsProperty(
                                          master_user_name=CfnDynamicReference(
                                              CfnDynamicReferenceService.SECRETS_MANAGER,
                                              f"{self.essecret.secret_name}:SecretString:username").to_string(),
                                          master_user_password=CfnDynamicReference(
                                              CfnDynamicReferenceService.SECRETS_MANAGER,
                                              f"{self.essecret.secret_name}:SecretString:password").to_string()
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
                                  #vpc_options=es.CfnDomain.VPCOptionsProperty(
                                  #    security_group_ids=[es_sg.security_group_id],
                                  #    subnet_ids=[vpc.public_subnets[0]]
                                  #),
                                )
        self.domain_endpoint = self.cfn_domain.attr_domain_endpoint
        self.cfn_domain.apply_removal_policy(policy=RemovalPolicy.DESTROY)
        CfnOutput(self, "opensearchdomain", value=self.cfn_domain.attr_domain_endpoint)


