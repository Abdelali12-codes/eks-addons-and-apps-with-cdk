from aws_cdk import (Resource, CfnOutput, Fn, RemovalPolicy)
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_certificatemanager as acm
import aws_cdk.aws_logs as logs
from ..configuration.config import *
from jinja2 import Environment, FileSystemLoader
import os
import yaml

DIR = os.path.dirname(os.path.realpath(__file__))

class ClientVpn(Resource):
    def __init__(self, scope, id, vpc_instance, **kwargs):
        super().__init__(scope, id)
        
        # Validate certificate configuration for mutual authentication
        self._validate_certificates()
        
        # Use the provided VPC instance
        self.vpc = vpc_instance.vpc
        
        # Create CloudWatch log group for VPN logs
        self.log_group = logs.LogGroup(
            self, f"{id}-LogGroup",
            log_group_name=f"/aws/clientvpn/{id}",
            retention=logs.RetentionDays.ONE_WEEK,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Create CloudWatch log stream
        self.log_stream = logs.LogStream(
            self, f"{id}-LogStream", 
            log_group=self.log_group,
            log_stream_name=f"{id}-stream"
        )

        # Create security group for VPN endpoint
        self.vpn_security_group = ec2.SecurityGroup(
            self, f"{id}-SecurityGroup",
            vpc=self.vpc,
            description="Security group for Client VPN endpoint",
            allow_all_outbound=True
        )

        # Allow HTTPS traffic for VPN connection
        self.vpn_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(443),
            description="Allow HTTPS for VPN"
        )

        # Get certificate ARNs from config for mutual authentication
        server_cert_arn = client_vpn_config.get('server_certificate_arn', 
            f"arn:aws:acm:{Fn.ref('AWS::Region')}:{Fn.ref('AWS::AccountId')}:certificate/{client_vpn_config.get('server_cert_id', 'YOUR_SERVER_CERT_ID')}")
        
        client_cert_arn = client_vpn_config.get('client_certificate_arn',
            f"arn:aws:acm:{Fn.ref('AWS::Region')}:{Fn.ref('AWS::AccountId')}:certificate/{client_vpn_config.get('client_cert_id', 'YOUR_CLIENT_CERT_ID')}")

        # Create Client VPN Endpoint with mutual authentication
        self.client_vpn_endpoint = ec2.CfnClientVpnEndpoint(
            self, f"{id}-Endpoint",
            client_cidr_block=client_vpn_config.get('client_cidr_block', '172.31.0.0/16'),
            server_certificate_arn=server_cert_arn,
            
            # Mutual authentication using certificates
            authentication_options=[
                {
                    "type": "certificate-authentication",
                    "mutualAuthentication": {
                        "clientRootCertificateChainArn": client_cert_arn
                    }
                }
            ],
            
            # Connection logging
            connection_log_options={
                "enabled": client_vpn_config.get('logging_enabled', True),
                "cloudwatchLogGroup": self.log_group.log_group_name,
                "cloudwatchLogStream": self.log_stream.log_stream_name
            },
            
            # VPN options from config
            dns_servers=client_vpn_config.get('dns_servers', ["8.8.8.8", "8.8.4.4"]),
            transport_protocol=client_vpn_config.get('transport_protocol', 'udp'),
            vpn_port=client_vpn_config.get('vpn_port', 443),
            
            # Security groups
            security_group_ids=[self.vpn_security_group.security_group_id],
            
            # VPC configuration
            vpc_id=self.vpc.vpc_id,
            
            # Optional configurations from config
            self_service_portal=client_vpn_config.get('self_service_portal', 'enabled'),
            session_timeout_hours=client_vpn_config.get('session_timeout_hours', 8),
            split_tunnel=client_vpn_config.get('split_tunnel', True),
            
            # Tags
            tag_specifications=[
                {
                    "resourceType": "client-vpn-endpoint",
                    "tags": [
                        {"key": "Name", "value": f"{id}-ClientVPN"},
                        {"key": "Environment", "value": client_vpn_config.get('environment', 'Development')},
                        {"key": "Project", "value": client_vpn_config.get('project_name', 'MyProject')}
                    ]
                }
            ]
        )

        # Associate VPN endpoint with subnets
        self.subnet_associations = []
        target_subnets = getattr(vpc_instance.vpc, client_vpn_config.get('target_subnet_type', 'private_subnets'))
        
        for i, subnet in enumerate(target_subnets):
            association = ec2.CfnClientVpnTargetNetworkAssociation(
                self, f"{id}-SubnetAssociation{i}",
                client_vpn_endpoint_id=self.client_vpn_endpoint.ref,
                subnet_id=subnet.subnet_id
            )
            self.subnet_associations.append(association)

        # Create authorization rules
        self._create_authorization_rules(id)
        
        # Create routes
        self._create_routes(id, target_subnets)

        # Outputs
        CfnOutput(
            self, f"{id}-EndpointId",
            value=self.client_vpn_endpoint.ref,
            description="Client VPN Endpoint ID",
            export_name=f"{id}-ClientVpnEndpointId"
        )

        CfnOutput(
            self, f"{id}-ClientCidrBlock",
            value=client_vpn_config.get('client_cidr_block', '172.31.0.0/16'),
            description="Client CIDR block for VPN connections",
            export_name=f"{id}-ClientCidrBlock"
        )

        # Store endpoint ID for reference
        self.endpoint_id = self.client_vpn_endpoint.ref

    def _validate_certificates(self):
        """Validate that required certificates are configured"""
        server_cert = client_vpn_config.get('server_certificate_arn') or client_vpn_config.get('server_cert_id')
        client_cert = client_vpn_config.get('client_certificate_arn') or client_vpn_config.get('client_cert_id')
        
        if not server_cert or server_cert == 'YOUR_SERVER_CERT_ID':
            raise ValueError("Server certificate ARN or ID must be configured for mutual authentication")
        
        if not client_cert or client_cert == 'YOUR_CLIENT_CERT_ID':
            raise ValueError("Client certificate ARN or ID must be configured for mutual authentication")
        
        return True

    def _create_authorization_rules(self, id):
        """Create authorization rules based on config"""
        auth_rules = client_vpn_config.get('authorization_rules', [])
        
        # Default VPC access rule
        if client_vpn_config.get('allow_vpc_access', True):
            self.auth_rule_vpc = ec2.CfnClientVpnAuthorizationRule(
                self, f"{id}-AuthRuleVPC",
                client_vpn_endpoint_id=self.client_vpn_endpoint.ref,
                target_network_cidr=self.vpc.vpc_cidr_block,
                authorize_all_groups=True,
                description="Allow access to VPC"
            )

        # Internet access rule
        if client_vpn_config.get('allow_internet_access', True):
            self.auth_rule_internet = ec2.CfnClientVpnAuthorizationRule(
                self, f"{id}-AuthRuleInternet",
                client_vpn_endpoint_id=self.client_vpn_endpoint.ref,
                target_network_cidr="0.0.0.0/0",
                authorize_all_groups=True,
                description="Allow internet access"
            )

        # Custom authorization rules from config
        for i, rule in enumerate(auth_rules):
            ec2.CfnClientVpnAuthorizationRule(
                self, f"{id}-AuthRuleCustom{i}",
                client_vpn_endpoint_id=self.client_vpn_endpoint.ref,
                target_network_cidr=rule.get('target_network_cidr'),
                authorize_all_groups=rule.get('authorize_all_groups', True),
                access_group_id=rule.get('access_group_id'),
                description=rule.get('description', f"Custom rule {i+1}")
            )

    def _create_routes(self, id, target_subnets):
        """Create routes based on config"""
        routes = client_vpn_config.get('routes', [])
        
        # Default internet route through NAT Gateway
        if client_vpn_config.get('internet_route_enabled', True):
            for i, subnet in enumerate(target_subnets):
                ec2.CfnClientVpnRoute(
                    self, f"{id}-InternetRoute{i}",
                    client_vpn_endpoint_id=self.client_vpn_endpoint.ref,
                    destination_cidr_block="0.0.0.0/0",
                    target_vpc_subnet_id=subnet.subnet_id,
                    description="Route to internet via NAT Gateway"
                )

        # Custom routes from config
        for i, route in enumerate(routes):
            for j, subnet in enumerate(target_subnets):
                ec2.CfnClientVpnRoute(
                    self, f"{id}-CustomRoute{i}Subnet{j}",
                    client_vpn_endpoint_id=self.client_vpn_endpoint.ref,
                    destination_cidr_block=route.get('destination_cidr_block'),
                    target_vpc_subnet_id=subnet.subnet_id,
                    description=route.get('description', f"Custom route {i+1}")
                )

    def get_endpoint_id(self):
        """Return the VPN endpoint ID for reference by other resources"""
        return self.endpoint_id