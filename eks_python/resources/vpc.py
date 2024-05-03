from aws_cdk import (Resource, CfnOutput, Fn)
import aws_cdk.aws_ec2 as ec2 
from ..configuration.config import *
from jinja2 import Environment, FileSystemLoader
import os 
import yaml

DIR = os.path.dirname(os.path.realpath(__file__))

class Vpc(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)
        
        # Vpc
        self.vpc = ec2.Vpc(self, f"{id}-Vpc",
                      ip_addresses=ec2.IpAddresses.cidr(vpc['vpccidr']),
                      enable_dns_hostnames= True,
                      enable_dns_support=True,
                      max_azs=vpc['max_azs'],
                      subnet_configuration=vpc['subnet_configuration']
            )
        
        # s3 endpoint
        self.vpc.add_gateway_endpoint(
            "s3endpoint",
            service= ec2.GatewayVpcEndpointAwsService.S3,
        )

        # dynamodb endpoint

        self.vpc.add_gateway_endpoint(
            "dyamodbendpoint",
            service=ec2.GatewayVpcEndpointAwsService.DYNAMODB
        )

        # sns endpoint

        self.vpc.add_interface_endpoint(
            "snsendpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SNS,
            private_dns_enabled= True,
            subnets= ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )

        # sqs endpoint

        self.vpc.add_interface_endpoint(
            "sqsendpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SQS,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )

        # ecr endpoint

        self.vpc.add_interface_endpoint(
            "ecrendpoint",
            service=ec2.InterfaceVpcEndpointAwsService.ECR,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )

        # ecr docker endpoint

        self.vpc.add_interface_endpoint(
            "ecrdockerendpoint",
            service=ec2.InterfaceVpcEndpointAwsService.ECR_DOCKER,
            private_dns_enabled= True,
            subnets= ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )

        # secretmanager
        secremanager = self.vpc.add_interface_endpoint(
            "secretmanager",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            private_dns_enabled= True,
            subnets= ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )

        # parameterstore
        self.vpc.add_interface_endpoint(
            "parameterstore",
            service=ec2.InterfaceVpcEndpointAwsService.SSM,
            private_dns_enabled= True,
            subnets= ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )

        # sts
        self.vpc.add_interface_endpoint(
            "stsassumerole",
            service=ec2.InterfaceVpcEndpointAwsService.STS,
            private_dns_enabled= True,
            subnets= ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )
        # cloudwatch

        self.vpc.add_interface_endpoint(
            "logsendpoint",
            service=ec2.InterfaceVpcEndpointAwsService.CLOUDWATCH_LOGS,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )

        # elasticloadbalancing

        self.vpc.add_interface_endpoint(
            "elasticloadbalancing",
            service=ec2.InterfaceVpcEndpointAwsService.ELASTIC_LOAD_BALANCING,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )

        # ec2

        self.vpc.add_interface_endpoint(
            "ec2",
            service=ec2.InterfaceVpcEndpointAwsService.EC2,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED)
        )
        
        self.private_subnets = [subnet.subnet_id for subnet in self.vpc.isolated_subnets]

        