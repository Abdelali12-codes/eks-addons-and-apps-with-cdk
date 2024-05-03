from aws_cdk import Resource
import aws_cdk.aws_eks as eks
import  aws_cdk.aws_ec2 as ec2
from ..policies.main import eksfargaterole


class FargateProfile(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id)
        
        eks_fargate_profile_role = eksfargaterole(self)
        cluster = None 
        namespaces = None 
        vpc = None
        items = {}


        if 'cluster' and 'namespaces' and 'vpc' in kwargs:
            cluster = kwargs['cluster']
            namespaces = kwargs['namespaces']
            vpc = kwargs['vpc']
        else:
            raise Exception('The cluster, namespaces and vpc arguments are missing')
        
        
        for namespace in namespaces:
            profile = cluster.add_fargate_profile(f"{id}-{namespace}",
              fargate_profile_name=namespace,
              selectors= [eks.Selector(namespace=namespace)],
              pod_execution_role= eks_fargate_profile_role,
              subnet_selection= ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
              vpc=vpc
            )

            items[namespace] = profile

        patch = eks.KubernetesPatch(self, "patchingcoredns", 
                                  cluster=cluster,
                                  resource_name="deployment/coredns",
                                  apply_patch={"spec": {"template": {"spec":{"schedulerName": "fargate-scheduler"}}}},
                                  restore_patch={"spec": {"template": {"spec":{"schedulerName": "default-scheduler"}}}},
                                  resource_namespace="kube-system"
                                )
            
        
        for namespace in namespaces:
            patch.node.add_dependency(items[namespace])