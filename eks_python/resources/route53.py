from aws_cdk import Resource
import aws_cdk.aws_route53 as route53
from ..configuration.config import *

class Route53Record(Resource):
    def __init__(self, scope, id, **kawrgs):
        super().__init__(scope, id)

        record = None 
        target = None
        hostedzone = None

        if 'service' and 'record_name' and 'target' and 'hosted_zone' in kawrgs:
          service = kawrgs['service']
          record = kawrgs['record_name']
          target = kawrgs['target']
          hostedzone = kawrgs['hosted_zone']
        else:
          raise Exception("The service arg should be provider")
        

        route53.ARecord(self, f"{id}-{service}-ARecord-{record.split('.')[0]}",
                      zone=hostedzone,
                      record_name=record,
                      target= target          
                    )
        
    