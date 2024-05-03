from aws_cdk import (Resource, Duration, CustomResource)
import aws_cdk.aws_lambda as _lambda
import aws_cdk.aws_iam as iam
import aws_cdk.custom_resources as custom
import os 
import json


DIR = os.path.dirname(os.path.realpath(__file__))

class CreateEsSecret(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)

        username = None
        secretname = None

        if 'username' in kwargs and 'secretname' in kwargs:
            username = kwargs['username']
            secretname = kwargs['secretname']
        else:
            raise Exception('you should provide the username and secret name')
        

        lambda_role = iam.Role(self, f"createsecret-lambda-role-{id}",
                             assumed_by= iam.ServicePrincipal('lambda.amazonaws.com'),
                             role_name="createsecret-lambda-role"
                            )
        policy = iam.Policy(self, "createsecret-lambda-policy", 
                            statements=[
                                iam.PolicyStatement(
                                    actions=["secretsmanager:*","lambda:*","ecr:*",
                                            "logs:CreateLogGroup",
                                            "logs:CreateLogStream",
                                            "logs:PutLogEvents"],
                                    resources=['*'],
                                    effect=iam.Effect.ALLOW
                                )
                            ]
                        )
        policy.attach_to_role(lambda_role)
        self.lambda_function = _lambda.Function(self, f'createessecret-{id}',
                              code= _lambda.Code.from_asset(os.path.join(DIR, 'code/')) ,
                              handler='main.handler',
                              runtime=_lambda.Runtime.PYTHON_3_12,
                              role=lambda_role,
                              function_name="create-es-secret",
                              timeout=  Duration.minutes(14)            
                            )
        
        self.custom = custom.AwsCustomResource(self, f'custom-es-secret-resource-{id}',
                            on_create=custom.AwsSdkCall(
                              action="Invoke",
                              service="lambda",
                              physical_resource_id= custom.PhysicalResourceId.of("createessecret"),
                              parameters={
                                  "FunctionName": self.lambda_function.function_name,
                                  "InvocationType": "RequestResponse",
                                  "Payload": json.dumps({
                                    "username": username,
                                    "secretname": secretname
                                  })
                              }
                           ),
                            on_delete=custom.AwsSdkCall(
                                action="DeleteSecret",
                                service="secrets-manager",
                                parameters={
                                    "SecretId": secretname,
                                    "ForceDeleteWithoutRecovery": "true"
                                }
                            ),
                            role=lambda_role  
                    )
        
        
        