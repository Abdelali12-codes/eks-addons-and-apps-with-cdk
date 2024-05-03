from aws_cdk import (Resource)
import aws_cdk.aws_sns as sns



class SnsTopic(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope,id)

        pass