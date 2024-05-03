from aws_cdk import CfnJson
import aws_cdk.aws_iam as iam
import aws_cdk.aws_eks as eks
import os 
import json


DIR = os.path.dirname(os.path.realpath(__file__))

def eks_node_role(self):
        
        iam_role = iam.Role(self, "noderole", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSWorkerNodePolicy"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKS_CNI_Policy"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
        policy = iam.Policy(self, f"lambda-policy-{id}", 
                            statements=[
                                iam.PolicyStatement(
                                    actions=[
                                            "route53:ChangeResourceRecordSets",
                                            "route53:ListResourceRecordSets"
                                    ],
                                    resources=['*'],
                                    effect=iam.Effect.ALLOW
                                ),
                                iam.PolicyStatement(
                                        effect= iam.Effect.ALLOW,
                                        actions=[
                                                "route53:ChangeResourceRecordSets",
                                                "route53:ListResourceRecordSets"
                                        ],
                                        resources=["arn:aws:route53:::change/*"]
                                )
                            ]
                        )
        policy.attach_to_role(iam_role)
        return iam_role
    
def eks_master_role(self):
        
        iam_role = iam.Role(self, "eksrole", assumed_by=iam.ServicePrincipal("eks.amazonaws.com"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSClusterPolicy"))
        
        return iam_role

def eksdescribeClusterpolicy(cluster):
        return iam.PolicyDocument(
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "eks:describe*"
                    ],
                    resources=[cluster.cluster_arn]
                )
            ]
        )

def eksfargaterole(self):
        return iam.Role(
                self,
                "eksfargateprofilerole",
                role_name= "eks-fargate-profile-role",
                assumed_by= iam.ServicePrincipal("eks-fargate-pods.amazonaws.com"),
                managed_policies= [iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSFargatePodExecutionRolePolicy")]
        )


def ExternalSecretServiceAccount(self, cluster):
        conditions = CfnJson(self, 'ConditionJson',
          value = {
            "%s:aud" % cluster.cluster_open_id_connect_issuer : "sts.amazonaws.com",
            "%s:sub" % cluster.cluster_open_id_connect_issuer : "system:serviceaccount:%s:%s" % ("external-secret","external-secret-sa"),
          },
        )

        role =  iam.Role(self, "ExternalSecretRole",
                          assumed_by=iam.OpenIdConnectPrincipal(cluster.open_id_connect_provider)
                                     .with_conditions({
                                        "StringEquals": conditions,
                                     }),
                                role_name="external-secret-role"
                        )
        
        policy = iam.Policy(self, "externalsecretpolicy",
                             statements=[
                                     iam.PolicyStatement(
                                             actions= [
                                                 "ssm:GetParameter*"
                                             ],
                                             resources=["*"],
                                             effect=iam.Effect.ALLOW
                                     ),
                                     iam.PolicyStatement(
                                             actions=[
                                                "secretsmanager:GetResourcePolicy",
                                                "secretsmanager:GetSecretValue",
                                                "secretsmanager:DescribeSecret",
                                                "secretsmanager:ListSecretVersionIds"    
                                             ],
                                             resources=["*"],
                                             effect=iam.Effect.ALLOW

                                     )
                             ])
        policy.attach_to_role(role=role)
        namespace = eks.KubernetesManifest(
                self,
                "externalsecretnamespace",
                cluster=cluster,
                manifest=[{
                       "apiVersion": "v1",
                       "kind": "Namespace",
                       "metadata": {"name": "external-secret"}
                }]
        )
        servicea = eks.ServiceAccount(self, 'externalsecretsa',
                           cluster=cluster,
                           name="external-secret-sa",
                           labels= {
                                "app.kubernetes.io/name": "external-secret-sa", 
                           },
                           annotations= {
                                "eks.amazonaws.com/role-arn": role.role_arn,
                           },
                           namespace="external-secret"
                        )
        servicea.node.add_dependency(namespace)



def lambdaRole(self, id):
        lambda_role = iam.Role(self, f"lambda-role-{id}",
                             assumed_by= iam.ServicePrincipal('lambda.amazonaws.com'),
                            )
        policy = iam.Policy(self, f"lambda-policy-{id}", 
                            statements=[
                                iam.PolicyStatement(
                                    actions=["elasticloadbalancing:*",
                                             "ec2:*", "logs:CreateLogGroup",
                                            "logs:CreateLogStream",
                                            "logs:PutLogEvents", "lambda:*"],
                                    resources=['*'],
                                    effect=iam.Effect.ALLOW
                                )
                            ]
                        )
        policy.attach_to_role(lambda_role)

        return lambda_role