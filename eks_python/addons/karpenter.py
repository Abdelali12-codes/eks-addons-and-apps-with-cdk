from aws_cdk import Resource, Stack, Duration
import aws_cdk.aws_ec2 as ec2
import aws_cdk.aws_iam as iam
import aws_cdk.aws_sqs as sqs
import aws_cdk.aws_events as events
import aws_cdk.aws_events_targets as events_target

from ..policies.main import karpenter_node_role, karpenter_controller_policy
from .custom_resources.tagresources import TagResource

class EksKarpenter(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)
        
        cluster = None 
        namespace = None
        

        if 'cluster' in kwargs and 'namespace' in kwargs:
            cluster = kwargs['cluster']
            namespace = kwargs['namespace']
        else:
            raise Exception('provide cluster and namespace attributes')
        
        TagResource(self, "tagresourcecustomresource",
                      cluster=cluster
                     )
        
        self.karpenternoderole = karpenter_node_role(self)

        instanceprofile = iam.CfnInstanceProfile(self, "karpenterinstanceprofile",
                              roles= [self.karpenternoderole.role_name],
                              instance_profile_name="karpenterinstanceprofile"                     
                            )
        
        cluster.aws_auth.add_role_mapping(self.karpenternoderole, username="system:node:{{EC2PrivateDNSName}}",
                                           groups=["system:bootstrappers", "system:nodes"])
        

        # create namespace
        self.namespace = cluster.add_manifest("karpenternamespace", {
            'apiVersion': 'v1',
            'kind': 'Namespace',
            'metadata': {
                'name': namespace,
            },
            })
        # create servicaccount
        self.serviceaccount  = cluster.add_service_account("karpentersa",
                              name="karpentersa",
                              namespace=namespace,                          
                            )
        self.serviceaccount.node.add_dependency(self.namespace)
        
        
        # create sqs
        karpenterqueue = sqs.Queue(self, "karpenterqueue",
                 queue_name="karpenterqueue",
                 retention_period= Duration.minutes(5)
                )
        
        # controller policy
        karpenter_controller_policy(self, sqsqueue=karpenterqueue,
                                     role=self.serviceaccount.role, 
                                     karpenternoderole=self.karpenternoderole)

        event_rules = [
            events.Rule(
                self,
                "ScheduledChangeRule",
                event_pattern={
                    "source": ['aws.ec2'],
                    "detail_type": ['EC2 Spot Instance Interruption Warning'],
                }
            ),

            events.Rule(
                self,
                "RebalanceRule",
                event_pattern={
                     "source": ['aws.ec2'],
                     "detail_type": ['EC2 Instance Rebalance Recommendation'],
                }
            ),
            events.Rule(
                self,
                "InstanceStateChangeRule",
                event_pattern={
                    "source": ['aws.ec2'],
                    "detail_type": ['EC2 Instance State-change Notification'],
                }
            )
        ]
        
        for rule in event_rules:
            rule.add_target(events_target.SqsQueue(karpenterqueue))


        # helm chart for karpenter
        karpenterchart = cluster.add_helm_chart("karpenterchart",
            wait=False,
            chart='karpenter',
            release='karpenter',
            repository="oci://public.ecr.aws/karpenter/karpenter",
            namespace=namespace,
            create_namespace=False,
            version="0.37.0",
            values={ 
                "serviceAccount": {
                    "create": False,
                    "name": self.serviceaccount.service_account_name,
                    "annotations": {
                        'eks.amazonaws.com/role-arn': self.serviceaccount.role.role_arn,
                    },
                },
                "settings":{
                        "clusterName": cluster.cluster_name,
                        "clusterEndpoint": cluster.cluster_endpoint,
                        "defaultInstanceProfile": instanceprofile.instance_profile_name,
                        "interruptionQueueName": karpenterqueue.queue_name
                }
            },
        )

        # karpenter nodeclass
        nodeclass = cluster.add_manifest("karpenternodeclass", {
            'apiVersion': 'karpenter.sh/v1',
            'kind': 'EC2NodeClass',
            'metadata': {
                'name': "default",
                'namespace': namespace
            },
            'spec':{
                'amiFamily': 'AL2',
                'subnetSelectorTerms':[
                    {
                        "tags":{
                           "karpenter.sh/discovery": cluster.cluster_name
                        }
                    }
                ],
                'securityGroupSelectorTerms':[
                    {
                        "tags":{
                            "karpenter.sh/discovery": cluster.cluster_name
                        }
                    }
                ],
                'role': self.karpenternoderole.role_name
            }
            })

        # karpenter nodepool
        nodepool = cluster.add_manifest("karpenternodepool", {
            'apiVersion': 'karpenter.sh/v1beta1',
            'kind': 'NodePool',
            'metadata': {
                'name': "default",
                'namespace': namespace
            },
            "spec":{
                "template":{
                       "spec":{
                            "requirements":[
                                {
                                    "key": "kubernetes.io/arch",
                                    "operator": "In",
                                    "values": ["amd64"]
                                },
                                {
                                    "key": "kubernetes.io/os",
                                    "operator": "In",
                                    "values": ["linux"]
                                },
                                {
                                    "key": "karpenter.k8s.aws/instance-category",
                                    "operator": "In",
                                    "values": ["t"]
                                },
                                {
                                    "key": "karpenter.k8s.aws/instance-family",
                                    "operator": "In",
                                    "values": ["t3"]
                                },
                                # {
                                #     "key": "karpenter.k8s.aws/instance-generation",
                                #     "operator": "Gt",
                                #     "values": ["2"]
                                # },
                                # {
                                #     "key": "karpenter.sh/capacity-type",
                                #     "operator": "In",
                                #     "values": ["spot"]
                                # },
                                {
                                    "key": "karpenter.k8s.aws/instance-size",
                                    "operator": "In",
                                    "values": ["small"]
                                }
                            ],
                            "nodeClassRef":{
                                "apiVersion": "karpenter.k8s.aws/v1beta1",
                                "kind": "EC2NodeClass",
                                "name": "default"
                            }
                       }
                },
                "limits":{
                   "cpu": "1000"
                },
                "disruption":{
                    "consolidationPolicy": "WhenUnderutilized",
                    "expireAfter": "720h"
                }
            }
  
            })
        
        nodeclass.node.add_dependency(karpenterchart)
        nodepool.node.add_dependency(karpenterchart)