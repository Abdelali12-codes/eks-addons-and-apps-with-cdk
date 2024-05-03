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

dnsconf = {
    "cert_arn_us_east_1": "arn:aws:acm:us-east-1:080266302756:certificate/326d29bd-95af-4139-ace0-eccb94dbbcfe", # us-east-1 region
    "cert_arn": "arn:aws:acm:us-east-2:080266302756:certificate/2d38c49e-009a-46b1-8bc2-571eebf19586", # us-west-3 for apigateway
    "domain": "abdelalitraining.com",
    "hostedzone_id": "Z05045244G4M5OFGHB4C"
}

cognitoconf = {
   "userpoolname": "microservicesapp",
   "appclient_name": "microservices",
   "domain-prefix": "microservice-application"
}


cldfront = {
  "record_names": ["cloudfrontapp1.abdelalitraining.com", "cloudfrontapp2.abdelalitraining.com"],
  "bucket_name": "react-app-cloudfront-26-02-2024"
}

apigaetway = {
    "api_record_name":"flaskrestapi.abdelalitraining.com"
}

rdsdb = {
   "instance_identifier":"rds-microservice",
   "secretname": "rdssecret",
   "allocated_storage": 40,
   "subnet_group_name": "rdsgroupname",
   "database_name": "microservice",
   "db_username": "abdelali",
   "instance_type": ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM)
}

opensearch = {
    "es_domain_name": "microservice-application",
    "secretname": "escredential" ,# secret that you store your es password
    "es_username": "esmicroservice",
    "capacity": {
        "data_nodes": 2,
        "data_node_instance_type":"t3.small.search"
    },
    "version":"OpenSearch_2.9",
    "ebs":es.CfnDomain.EBSOptionsProperty(
        ebs_enabled= True,
        volume_size=100,
        volume_type= "gp2"
    )
      
}

dynamo = {
    "tables": [
        {
            "table_name": "firsttable",
            "partition_key": dynamodb.Attribute(
                name="name",
                type=dynamodb.AttributeType.STRING
            ),
            "sort_key": dynamodb.Attribute(
                name="birthday",
                type=dynamodb.AttributeType.STRING
            )
        }
    ]
}

def hostedzone(self):
    return route53.HostedZone.from_hosted_zone_attributes(self, "route53hosedzone", hosted_zone_id= dnsconf['hostedzone_id'],
                      zone_name=dnsconf['domain']                              
                    )