import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_opensearchservice as es
import aws_cdk.aws_route53 as route53
import aws_cdk.aws_dynamodb as dynamodb

REGION = "us-east-2"
ACCOUNT = "080266302756"

vpc  = {
    "vpccidr": "12.10.0.0/16",
    "subnet_configuration": [
        ec2.SubnetConfiguration(
            name = "public-subnet",
            subnet_type = ec2.SubnetType.PUBLIC,
            cidr_mask=24,
        ),
        ec2.SubnetConfiguration( 
            name="isolated-subnet",
            subnet_type= ec2.SubnetType.PRIVATE_ISOLATED,
            cidr_mask=24
        ),
    ],
    "max_azs": 2,
 }

rdsdb = {
   "instance_identifier":"rds-airflow",
   "secretname": "rdssecret",
   "allocated_storage": 40,
   "subnet_group_name": "rdsgroupname",
   "database_name": "airflow",
   "db_username": "airflow",
   "instance_type": ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM)
}

argocd = {
    "hostname": "argocd.abdelalitraining.com",
    "manifestrepo": "git@github.com:Abdelali12-codes/flask-app-k8s-manifests-gitops.git"
}
dexapplications = {
    "github":{
      "clientid": "xxxxxxxxxxxxxxxxxx",
      "clientsecret": "xxxxxxxxxxxxxxxxxxxxxxxx"
    },
    "gitlab": {
      "clientid": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
      "clientsecret": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
    }
}

clusterissuer = {
    "email": "jadelmoulaa2@gmail.com", # change it to yours
    "hostedZoneName": "abdelalitraining.com", # change it to yours
    "hostedZoneID": "Z05045244G4M5OFGHB4C", # change it to yours
}

opensearch = {
    "es_domain_name": "microservice-application",
    "secretname": "escredential",  # secret that you store your es password
    "es_username": "esmicroservice",
    "capacity": {
        "data_nodes": 2,
        "data_node_instance_type": "t3.small.search"
    },
    "version": "OpenSearch_2.9",
    "ebs": es.CfnDomain.EBSOptionsProperty(
        ebs_enabled=True,
        volume_size=100,
        volume_type="gp2"
    )
}

client_vpn_config = {
    # Basic VPN settings
    'client_cidr_block': '172.31.0.0/16',  # CIDR block for VPN clients
    'dns_servers': ['8.8.8.8', '8.8.4.4'],
    'transport_protocol': 'udp',  # 'udp' or 'tcp'
    'vpn_port': 443,
    
    # Mutual Authentication Certificate settings
    # Option 1: Provide certificate IDs (ARNs will be constructed)
    'server_cert_id': 'YOUR_SERVER_CERT_ID',  # Replace with actual certificate ID from ACM
    'client_cert_id': 'YOUR_CLIENT_CERT_ID',  # Replace with actual certificate ID from ACM
    
    # Option 2: Provide full ARNs directly (these will override the IDs above)
    # 'server_certificate_arn': 'arn:aws:acm:region:account:certificate/server-cert-id',
    # 'client_certificate_arn': 'arn:aws:acm:region:account:certificate/client-cert-id',
    
    # VPN behavior settings
    'self_service_portal': 'enabled',  # 'enabled' or 'disabled'
    'session_timeout_hours': 8,
    'split_tunnel': True,
    'logging_enabled': True,
    
    # Network settings
    'target_subnet_type': 'private_subnets',  # 'private_subnets', 'public_subnets', or 'isolated_subnets'
    'allow_vpc_access': True,
    'allow_internet_access': True,
    'internet_route_enabled': True,
    
    # Tags
    'environment': 'Production',
    'project_name': 'MyProject',
    
    # Custom authorization rules (optional)
    'authorization_rules': [
        # {
        #     'target_network_cidr': '10.1.0.0/16',
        #     'authorize_all_groups': True,
        #     'access_group_id': None,  # Optional: specific group ID
        #     'description': 'Allow access to specific network'
        # }
    ],
    
    # Custom routes (optional)
    'routes': [
        # {
        #     'destination_cidr_block': '192.168.1.0/24',
        #     'description': 'Route to on-premises network'
        # }
    ]
}