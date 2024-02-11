from aws_cdk import Resource



class RdsDatabase(Resource):
    def __init_(self, scope, id, **kwargs):
        super().__init__(scope, id)
        
        
        ### logic