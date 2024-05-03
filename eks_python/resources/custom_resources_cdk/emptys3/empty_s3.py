from aws_cdk import (Resource, Duration, CustomResource)
import aws_cdk.aws_lambda as _lambda
import aws_cdk.aws_iam as iam
import aws_cdk.custom_resources as custom
import os 


DIR = os.path.dirname(os.path.realpath(__file__))

class EmptyS3(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)

        BucketName = None 

        if 'BucketName' in kwargs:
            BucketName = kwargs['BucketName']
        else:
            raise Exception('you should provide the bukcetname you want to empty')
        
        lambda_role = iam.Role(self, f"lambda-role-{id}",
                             assumed_by= iam.ServicePrincipal('lambda.amazonaws.com')   
                            )
        policy = iam.Policy(self, "lambda-policy", 
                            statements=[
                                iam.PolicyStatement(
                                    actions=['s3:*'],
                                    resources=['*'],
                                    effect=iam.Effect.ALLOW
                                )
                            ]
                        )
        policy.attach_to_role(lambda_role)

        lambda_function = _lambda.Function(self, 'emptys3',
                              code= _lambda.Code.from_asset(os.path.join(DIR, 'code/')) ,
                              handler='main.handler',
                              runtime=_lambda.Runtime.PYTHON_3_12,
                              function_name="emptys3",
                              timeout=  Duration.minutes(3)            
                            )
        
        custom.AwsCustomResource(self, f'customresource-{id}',
                       on_delete=custom.AwsSdkCall(
                              action="InvokeFunction",
                              service="lambda",
                              parameters={
                                  "FunctionName": lambda_function.function_name,
                                  "Payload": {
                                   "BucketName": BucketName
                                  }
                              }
                           ),
                    )
        