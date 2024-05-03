from constructs import Construct
from aws_cdk import (CfnOutput, Stack)
import  aws_cdk.aws_iam as iam
from ..policies.main import eksdescribeClusterpolicy


class EksAuth(Construct):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)
        cluster = None
        node_role = None
        ## logic
        if 'cluster' and 'node_role'  in kwargs:
            cluster = kwargs['cluster']
            node_role = kwargs['node_role']

        else:
            raise Exception("cluster param is not present")
        
        ## describe permissions
        describecluster = eksdescribeClusterpolicy(cluster)

        role = iam.Role(self, 'eksauthrole',
              assumed_by=  iam.AccountRootPrincipal(),
              role_name= "eksauthrole",
              inline_policies= {
                  "describecluster": describecluster
              }     
            )
        
        cluster.aws_auth.add_role_mapping(node_role, username="system:node:{{EC2PrivateDNSName}}", groups=["system:bootstrappers", "system:nodes"])
        cluster.aws_auth.add_role_mapping(role, username= "rootrole", groups= ['system:masters']),

       
        ### output role arn
        CfnOutput(self, "authrolearn", value=role.role_arn)
        