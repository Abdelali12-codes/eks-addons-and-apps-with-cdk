from aws_cdk import Resource
from constructs import Construct





class ApiGateway(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope,id)
        ## logic