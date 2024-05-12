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
   "instance_identifier":"rds-microservice",
   "secretname": "rdssecret",
   "allocated_storage": 40,
   "subnet_group_name": "rdsgroupname",
   "database_name": "microservice",
   "db_username": "abdelali",
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