from aws_cdk import (Resource, Duration, Stack)
import aws_cdk.aws_lambda as _lambda
import aws_cdk.aws_iam as iam
import aws_cdk.aws_secretsmanager as sm
import aws_cdk.aws_ec2 as ec2
import aws_cdk.custom_resources as custom
import os 
import json


DIR = os.path.dirname(os.path.realpath(__file__))

class RdsLambda(Resource):
    def __init__(self, scope, id, vpc, secret: sm.ISecret, **kwargs):
        super().__init__(scope, id)

        lambda_role = iam.Role(self, f"rds-databases-role-{id}",
                             assumed_by= iam.ServicePrincipal('lambda.amazonaws.com'),
                             role_name="rds-databases-lambda-role",
                             managed_policies= [iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaVPCAccessExecutionRole")]
                            )
        policy = iam.Policy(self, "rds-databases-policy",
                            statements=[
                                iam.PolicyStatement(
                                    actions=[
                                            "secretsmanager:*",
                                            "logs:CreateLogGroup",
                                            "logs:CreateLogStream",
                                            "logs:PutLogEvents",
                                            "lambda:InvokeFunction"
                                        ],
                                    resources=['*'],
                                    effect=iam.Effect.ALLOW
                                )
                            ]
                        )
        policy.attach_to_role(lambda_role)
        lambda_layer = _lambda.LayerVersion(self, "rds-databases-lambda-layer",
                                    layer_version_name="rds-databases-lambda-layer",
                                    description="Layer with psycopg library",
                                    code=_lambda.Code.from_asset(os.path.join(DIR, 'lambda_layer')),
                                    compatible_runtimes=[_lambda.Runtime.PYTHON_3_12]
                                    )
        
        self.lambda_function = _lambda.Function(self, f'createrdsdbs-{id}',
                              code= _lambda.Code.from_asset(os.path.join(DIR, 'code/')) ,
                              handler='main.lambda_handler',
                              runtime=_lambda.Runtime.PYTHON_3_12,
                              role=lambda_role,
                              environment={
                                  "SECRET_NAME": secret.secret_name
                              },
                              function_name="rds-databases",
                              timeout=  Duration.minutes(14),
                              layers=[lambda_layer],
                              vpc= vpc,
                              vpc_subnets= ec2.SubnetSelection(
                                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                                )
                            )
        
        self.custom = custom.AwsCustomResource(self, f'custom-rds-databases-{id}',
                            on_create=custom.AwsSdkCall(
                              action="Invoke",
                              service="lambda",
                              physical_resource_id= custom.PhysicalResourceId.of("rdsdatabases"),
                              parameters={
                                  "FunctionName": self.lambda_function.function_name,
                                  "InvocationType": "RequestResponse"
                              }
                            ),
                            #on_delete=custom.AwsSdkCall(
                            #    action="DeleteSecret",
                            #    service="secrets-manager",
                            #    parameters={
                            #        "SecretId": secretname,
                            #        "ForceDeleteWithoutRecovery": "true"
                            #    }
                            #),
                            role=lambda_role  
                    )
        
        
        