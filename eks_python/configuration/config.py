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

