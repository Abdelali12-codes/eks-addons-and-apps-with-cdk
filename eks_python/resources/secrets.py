from aws_cdk import (Resource, RemovalPolicy,CfnDynamicReference, CfnDynamicReferenceService, CfnOutput)
import aws_cdk.aws_rds as rds
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_secretsmanager as secret
import aws_cdk.aws_ssm as ssm
from ..configuration.config import rdsdb
import json

class KeycloakSecret(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)
        

        self.keycloaksecret = secret.Secret(self, "keycloaksecret", 
                          generate_secret_string= secret.SecretStringGenerator(
                              secret_string_template= json.dumps({"username":"admin"}),
                              exclude_punctuation=True,
                              password_length=16,
                              generate_string_key="password"
                          )         
                        )
        
        