from aws_cdk import (Resource, RemovalPolicy,CfnDynamicReference, CfnDynamicReferenceService, CfnOutput)
import aws_cdk.aws_rds as rds
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_secretsmanager as secret
from ..configuration.config import rdsdb
import json


class RdsDatabase(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)

        vpc = None

        if 'vpc' in kwargs:
            vpc = kwargs['vpc']
        else:
            raise Exception('Please Provide the vpc arg')
        
        vpc = kwargs['vpc']

        db_sg = ec2.SecurityGroup(self, "SecurityGroup",
            vpc=vpc,
            description="rds-microservices-sg",
            security_group_name="rds-microservices-sg",
            allow_all_outbound=True,
        )

        db_sg.add_ingress_rule(ec2.Peer.ipv4(vpc.vpc_cidr_block), ec2.Port.tcp(5432), "allow postgres")

        subnet_group = rds.SubnetGroup(self, f"{id}-subnetgroup",
            description="description",
            vpc=vpc,
            removal_policy=RemovalPolicy.DESTROY,
            subnet_group_name=rdsdb["subnet_group_name"],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            )
        )
        # db script
        self.dbsecret = secret.Secret(self, "rdssecret", 
                          secret_name=rdsdb['secretname'],
                          generate_secret_string= secret.SecretStringGenerator(
                              secret_string_template= json.dumps({"username":rdsdb["db_username"]}),
                              exclude_punctuation=True,
                              password_length=16,
                              generate_string_key="password"
                          )         
                        )

        db_rds = rds.DatabaseInstance(self, f"{id}-rdsinstance",
                instance_identifier=rdsdb["instance_identifier"],
                database_name=rdsdb["database_name"],
                engine=rds.DatabaseInstanceEngine.POSTGRES,
                allocated_storage= rdsdb["allocated_storage"],
                instance_type=rdsdb["instance_type"],
                vpc_subnets= ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
                credentials=rds.Credentials.from_secret(self.dbsecret),
                vpc=vpc,
                storage_type= rds.StorageType.GP2,
                subnet_group= subnet_group,
                removal_policy= RemovalPolicy.DESTROY,
            )
        
        self.rds_endpoint = db_rds.db_instance_endpoint_address
        
        


        # database endpoint
        CfnOutput(self, 'dbendpoint', value=db_rds.db_instance_endpoint_address)