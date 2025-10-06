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
                      nat_gateways=1,
                      max_azs=vpc['max_azs'],
                      subnet_configuration=vpc['subnet_configuration'],
            )
       
        self.private_subnets = [subnet.subnet_id for subnet in self.vpc.isolated_subnets]
        self.public_subnets  = [subnet.subnet_id for subnet in self.vpc.public_subnets]

        