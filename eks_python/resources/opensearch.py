from aws_cdk import Resource


class Opensearch(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)
        
        
        ### logic