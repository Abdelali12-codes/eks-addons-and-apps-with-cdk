from aws_cdk import (Resource)

class SqsMessage(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)
        pass