from aws_cdk import (Resource, Duration, CustomResource)
import aws_cdk.aws_lambda as _lambda
import aws_cdk.aws_iam as iam
import aws_cdk.custom_resources as custom
import os 
import json


DIR = os.path.dirname(os.path.realpath(__file__))

class TagResource(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)


        cluster = None 
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception('The resource expect cluster arg')
  
        lambda_role = iam.Role(self, f"tagresources-{id}",
                             assumed_by= iam.ServicePrincipal('lambda.amazonaws.com'),
                             role_name="tagresources"
                            )
        policy = iam.Policy(self, "tagresources-lambda-policy", 
                            statements=[
                                iam.PolicyStatement(
                                    actions=["lambda:*",
                                            "logs:CreateLogGroup",
                                            "logs:CreateLogStream",
                                             "eks:Describe*","ec2:*","eks:ListNodegroups",
                                            "logs:PutLogEvents"],
                                    resources=['*'],
                                    effect=iam.Effect.ALLOW
                                )
                            ]
                        )
        policy.attach_to_role(lambda_role)
        self.lambda_function = _lambda.Function(self, f'tagresources-lambda-{id}',
                              code= _lambda.Code.from_asset(os.path.join(DIR, 'code/')) ,
                              handler='main.lambda_handler',
                              runtime=_lambda.Runtime.PYTHON_3_12,
                              role=lambda_role,
                              function_name="tagresources",
                              timeout=  Duration.minutes(2)            
                            )
        
        self.custom = custom.AwsCustomResource(self, f'custom-tagresources-{id}',
                            on_create=custom.AwsSdkCall(
                              action="Invoke",
                              service="lambda",
                              physical_resource_id= custom.PhysicalResourceId.of("tagresources"),
                              
                              parameters={
                                  "FunctionName": self.lambda_function.function_name,
                                  "InvocationType": "RequestResponse",
                                  "Payload": json.dumps({
                                    "cluster": cluster.cluster_name
                                  })
                              }
                           ),
                           role=lambda_role
                    )
        self.custom.node.add_dependency(cluster)
        
        