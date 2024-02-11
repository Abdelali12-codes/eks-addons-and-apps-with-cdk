from aws_cdk import Resource
import aws_cdk.aws_ec2 as ec2 
from ..configuration.config import *

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