from aws_cdk import (Resource, Duration, Stack)
import aws_cdk.aws_lambda as _lambda
import aws_cdk.aws_iam as iam
import aws_cdk.custom_resources as custom
import os 
import json


DIR = os.path.dirname(os.path.realpath(__file__))

class EsMapping(Resource):
    def __init__(self, scope, id,  esdomaine, secretname, fluentbitrolearn , **kwargs):
        super().__init__(scope, id)

        lambda_role = iam.Role(self, f"getsecret-lambda-role-{id}",
                             assumed_by= iam.ServicePrincipal('lambda.amazonaws.com'),
                             role_name="getsecret-lambda-role"
                            )
        policy = iam.Policy(self, "getsecret-policy",
                            statements=[
                                iam.PolicyStatement(
                                    actions=[
                                            "secretsmanager:*",
                                            "es:ESHttp*",
                                            "logs:CreateLogGroup",
                                            "logs:CreateLogStream",
                                            "logs:PutLogEvents"],
                                    resources=['*'],
                                    effect=iam.Effect.ALLOW
                                )
                            ]
                        )
        policy.attach_to_role(lambda_role)
        lambda_layer = _lambda.LayerVersion(self, "es-lambda-layer",
                                    layer_version_name="es-lambda-layer",
                                    description="Layer with requests library",
                                    code=_lambda.Code.from_asset(os.path.join(DIR, 'lambda_layer')),
                                    compatible_runtimes=[_lambda.Runtime.PYTHON_3_12]
                                    )
        self.lambda_function = _lambda.Function(self, f'createessecret-{id}',
                              code= _lambda.Code.from_asset(os.path.join(DIR, 'code/')) ,
                              handler='main.handler',
                              runtime=_lambda.Runtime.PYTHON_3_12,
                              role=lambda_role,
                              environment={
                                  "SECRET_NAME": secretname,
                                  "REGION_NAME": Stack.of(self).region,
                                  "OPENSEARCH_ENDPOINT": esdomaine,
                                  "ROLE_NAME": fluentbitrolearn
                              },
                              function_name="es-mappings",
                              timeout=  Duration.minutes(14),
                              layers=[lambda_layer]
                            )
        
        self.custom = custom.AwsCustomResource(self, f'custom-es-secret-resource-{id}',
                            on_create=custom.AwsSdkCall(
                              action="Invoke",
                              service="lambda",
                              physical_resource_id= custom.PhysicalResourceId.of("createessecret"),
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
        
        
        