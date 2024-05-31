import os
import boto3

def lambda_handler(event, context):

    if 'cluster' not in event:
        raise Exception('the lambda expect cluster attribute in event')
    cluster_name = event['cluster']
    
    eks_client = boto3.client('eks')
    ec2_client = boto3.client('ec2')
    
    # Get the list of nodegroups
    nodegroups_response = eks_client.list_nodegroups(
        clusterName=cluster_name
    )
    nodegroups = nodegroups_response['nodegroups']
    
    # Describe the cluster to get the security groups
    cluster_details = eks_client.describe_cluster(
        name=cluster_name
    )
    security_groups = [cluster_details['cluster']['resourcesVpcConfig']['clusterSecurityGroupId']]
    
    # Create tags for the security groups
    ec2_client.create_tags(
        Resources=security_groups,
        Tags=[
            {
                'Key': 'karpenter.sh/discovery',
                'Value': cluster_name
            }
        ]
    )
    
    # Iterate over each nodegroup
    for nodegroup in nodegroups:
        # Describe the nodegroup to get the subnets
        nodegroup_details = eks_client.describe_nodegroup(
            clusterName=cluster_name,
            nodegroupName=nodegroup
        )
        subnets = nodegroup_details['nodegroup']['subnets']
        
        # Create tags for the subnets
        ec2_client.create_tags(
            Resources=subnets,
            Tags=[
                {
                    'Key': 'karpenter.sh/discovery',
                    'Value': cluster_name
                }
            ]
        )
    
    return {
        'statusCode': 200,
        'body': f'Successfully tagged subnets and security groups for nodegroups: {nodegroups}'
    }
