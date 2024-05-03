from aws_cdk import (Resource, Duration, CustomResource)
import aws_cdk.aws_lambda as _lambda
import aws_cdk.aws_iam as iam
import aws_cdk.custom_resources as custom
import os 
import json


DIR = os.path.dirname(os.path.realpath(__file__))

class DescribeElb(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)

        ELBName = None 

        if 'ELBName' in kwargs:
            ELBName = kwargs['ELBName']
        else:
            raise Exception('you should provide the elbname you want to delete')
        

        lambda_role = iam.Role(self, f"lambda-role-{id}",
                             assumed_by= iam.ServicePrincipal('lambda.amazonaws.com'),
                            )
        policy = iam.Policy(self, "lambda-policy", 
                            statements=[
                                iam.PolicyStatement(
                                    actions=["elasticloadbalancing:*","ecr:*",
                                             "ec2:*", "logs:CreateLogGroup",
                                            "logs:CreateLogStream",
                                            "logs:PutLogEvents", "lambda:*", "secretsmanager:*"],
                                    resources=['*'],
                                    effect=iam.Effect.ALLOW
                                )
                            ]
                        )
        policy.attach_to_role(lambda_role)
        self.lambda_function = _lambda.Function(self, f'deleteelb-{id}',
                              code= _lambda.Code.from_asset(os.path.join(DIR, 'code/')) ,
                              handler='main.handler',
                              runtime=_lambda.Runtime.PYTHON_3_12,
                              role=lambda_role,
                              function_name="describe-elb",
                              timeout=  Duration.minutes(14)            
                            )
        
        self.custom = custom.AwsCustomResource(self, f'customresource-{id}',
                            on_delete=custom.AwsSdkCall(
                              action="Invoke",
                              service="lambda",
                              parameters={
                                  "FunctionName": self.lambda_function.function_name,
                                  "InvocationType": "RequestResponse",
                                  "Payload": json.dumps({
                                    "ELBName": ELBName
                                  })
                              }
                           ),
                        role=lambda_role       
                    )
        
        
        