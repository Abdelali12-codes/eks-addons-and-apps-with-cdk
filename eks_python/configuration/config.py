import aws_cdk.aws_ec2 as ec2

vpc  = {
    "vpccidr": "12.10.0.0/16",
    "subnet_configuration": [
        ec2.SubnetConfiguration(
            name = "public-subnet",
            subnet_type = ec2.SubnetType.PUBLIC,
            cidr_mask=24
        )
    ],
    "max_azs": 2,
 }