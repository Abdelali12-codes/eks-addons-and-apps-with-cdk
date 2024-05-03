from aws_cdk import Resource, RemovalPolicy
import aws_cdk.aws_dynamodb as dynamodb
from ..configuration.config import dynamo


class DynamodbTable(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)

        for table in dynamo['tables']:
            if 'table_name' and 'partition_key' in table:
                item = dynamodb.Table(self, f"{id}-${table['table_name']}",
                            table_name=table['table_name'],
                            partition_key=table['partition_key'],
                            sort_key=table['sort_key'] if 'sort_key' in table else None,
                            read_capacity= table['read_capacity'] if  'read_capacity' in table else 5,
                            write_capacity= table['write_capacity'] if 'write_capacity' in table else 5,
                            removal_policy= RemovalPolicy.DESTROY
                )
            else:
                raise Exception('you need to provide the table name and partition key')
