from aws_cdk import CfnJson, Stack
import aws_cdk.aws_iam as iam
import aws_cdk.aws_eks as eks
import aws_cdk.aws_sqs as sqs
import os 
import json


DIR = os.path.dirname(os.path.realpath(__file__))

def eks_node_role(self):
        
        iam_role = iam.Role(self, "noderole", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"), role_name="eks-worker-node-role")
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSWorkerNodePolicy"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKS_CNI_Policy"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
        policy = iam.Policy(self, f"lambda-policy-{id}", 
                            statements=[
                                iam.PolicyStatement(
                                    actions=[
                                            "route53:ListHostedZonesByName"
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
                                        resources=["arn:aws:route53:::hostedzone/*"]
                                ),
                                iam.PolicyStatement(
                                        actions= [
                                                "route53:GetChange"
                                        ],
                                        effect=iam.Effect.ALLOW,
                                        resources=[
                                                "arn:aws:route53:::change/*"
                                        ]
                                )
                            ]
                        )
        policy.attach_to_role(iam_role)
        return iam_role

def karpenter_node_role(self):
        iam_role = iam.Role(self, "noderole", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"), role_name="karpenter-worker-node-role")
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSWorkerNodePolicy"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKS_CNI_Policy"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")) 

        return iam_role

def karpenter_controller_policy(self, sqsqueue: sqs.Queue, role: iam.Role, karpenternoderole: iam.Role):
        policy = iam.Policy(self, "karpentercontrollerpolicy",
                    statements=[
                           iam.PolicyStatement(
                                  effect= iam.Effect.ALLOW,
                                  actions=[
                                          "ec2:CreateLaunchTemplate",
                                          "ec2:CreateFleet",
                                          "ec2:RunInstances",
                                          "ec2:CreateTags",
                                          "ec2:TerminateInstances",
                                          "ec2:DescribeLaunchTemplates",
                                          "ec2:DescribeInstances",
                                          "ec2:DescribeSecurityGroups",
                                          "ec2:DeleteLaunchTemplate",
                                          "ec2:DescribeSubnets",
                                          "ec2:DescribeImages",
                                          "ec2:DescribeInstanceTypes",
                                          "ec2:DescribeInstanceTypeOfferings",
                                          "ec2:DescribeAvailabilityZones",
                                          "ec2:DescribeSpotPriceHistory",
                                          "pricing:GetProducts",
                                          "iam:AddRoleToInstanceProfile",
                                          "iam:RemoveRoleFromInstanceProfile",
                                          "iam:DeleteInstanceProfile",
                                          "iam:GetInstanceProfile",
                                          "iam:CreateInstanceProfile",
                                          "iam:TagInstanceProfile",
                                          "eks:DescribeCluster",
                                          "ssm:GetParameter"
                                  ],
                                  resources=["*"]
                           ),
                           iam.PolicyStatement(
                                  effect=iam.Effect.ALLOW,
                                  actions=[
                                        'sqs:DeleteMessage',
                                        'sqs:GetQueueAttributes',
                                        'sqs:GetQueueUrl',
                                        'sqs:ReceiveMessage',
                                  ],
                                  resources=[sqsqueue.queue_arn]
                           ),
                           iam.PolicyStatement(
                                  effect= iam.Effect.ALLOW,
                                  actions=[
                                        "iam:PassRole"
                                  ],
                                  resources=[karpenternoderole.role_arn]
                           )
                    ]
               )
        policy.attach_to_role(role)
       

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



def AirflowServiceAccount(self, cluster) -> iam.IRole:
        conditions = CfnJson(self, 'ConditionJson',
          value = {
            "%s:aud" % cluster.cluster_open_id_connect_issuer : "sts.amazonaws.com",
            "%s:sub" % cluster.cluster_open_id_connect_issuer : "system:serviceaccount:%s:%s" % ("airflow","airflow-sa"),
          },
        )

        role =  iam.Role(self, "AirflowRole",
                          assumed_by=iam.OpenIdConnectPrincipal(cluster.open_id_connect_provider)
                                     .with_conditions({
                                        "StringEquals": conditions,
                                     }),
                                role_name="airflow-role"
                        )
        
        policy = iam.Policy(self, "airflowpolicy",
                             statements=[
                                     
                                     iam.PolicyStatement(
                                             actions=[
                                                "s3:ListBucket",
                                                "s3:GetObject",
                                                "s3:PutObject"
                                             ],
                                             resources=["*"],
                                             effect=iam.Effect.ALLOW

                                     )
                             ])
        policy.attach_to_role(role=role)
        servicea = eks.ServiceAccount(self, 'airflowsa',
                           cluster=cluster,
                           name="airflow-sa",
                           labels= {
                                "app.kubernetes.io/name": "airflow-sa",
                                "app.kubernetes.io/managed-by": "Helm",
                           },
                           annotations= {
                                "eks.amazonaws.com/role-arn": role.role_arn,
                                "meta.helm.sh/release-name": "airflow", 
                                "meta.helm.sh/release-namespace": "airflow"
                           },
                           namespace="airflow"
                        )
        return role



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
def ExternalDnsRole(self, cluster):
        conditions = CfnJson(self, 'ConditionJson',
          value = {
            "%s:aud" % cluster.cluster_open_id_connect_issuer : "sts.amazonaws.com",            # namespace # serviceaccountname
            "%s:sub" % cluster.cluster_open_id_connect_issuer : "system:serviceaccount:%s:%s" % ("default","external-dns"),
          },
        )

        role =  iam.Role(self, "ExternalDnsRole",
                          assumed_by=iam.OpenIdConnectPrincipal(cluster.open_id_connect_provider)
                                     .with_conditions({
                                        "StringEquals": conditions,
                                     }),
                                role_name="external-dns-role"
                        )
        statements = []
        with open(os.path.join(DIR, 'external_dns_policy.json'), 'r') as f:
                data = json.load(f)
                for s in data['Statement']:
                    statements.append(iam.PolicyStatement.from_json(s))

        policy = iam.Policy(self, "externaldnspolicy",statements=statements, policy_name="externaldnspolicy")

        policy.attach_to_role(role)
        return role

def CertManagerRole(self, cluster, noderole):
        
        statements = []
        with open(os.path.join(DIR, 'external_dns_policy.json'), 'r') as f:
                data = json.load(f)
                for s in data['Statement']:
                    statements.append(iam.PolicyStatement.from_json(s))

        policy = iam.Policy(self, "externaldnspolicy",statements=statements, policy_name="externaldnspolicy")

        certmanagerrole = iam.Role(self, "certmanagerrole", 
                                   assumed_by=iam.ArnPrincipal(noderole.role_arn), role_name="certmanagerrole")
        
        policy.attach_to_role(certmanagerrole)
        return certmanagerrole

def S3DriverMountServicea(self, cluster):
        conditions = CfnJson(self, 'ConditionJson',
          value = {
            "%s:aud" % cluster.cluster_open_id_connect_issuer : "sts.amazonaws.com",            # namespace # serviceaccountname
            "%s:sub" % cluster.cluster_open_id_connect_issuer : "system:serviceaccount:%s:%s" % ("kube-system","s3-csi-driver-sa"),
          },
         )

        role =  iam.Role(self, "S3DriverMountRole",
                          assumed_by=iam.OpenIdConnectPrincipal(cluster.open_id_connect_provider)
                                     .with_conditions({
                                        "StringEquals": conditions,
                                     }),
                                role_name="S3DriverMountRole"
                        )
        
        policy = iam.Policy(self, "s3driverpolicy",
                             statements=[
                                     iam.PolicyStatement(
                                             actions= [
                                                 "s3:ListBucket"
                                             ],
                                             resources=["*"],
                                             effect=iam.Effect.ALLOW
                                     ),
                                     iam.PolicyStatement(
                                             actions=[
                                                "s3:GetObject",
                                                "s3:PutObject",
                                                "s3:AbortMultipartUpload",
                                                "s3:DeleteObject"
                                             ],
                                             resources=["*"],
                                             effect=iam.Effect.ALLOW

                                     )
                             ])
        
        policy.attach_to_role(role)
        
        servicea = eks.ServiceAccount(self, 's3-csi-driver-sa',
                           cluster=cluster,
                           name="s3-csi-driver-sa",
                           labels= {
                                "app.kubernetes.io/name": "s3-csi-driver-sa",
                                "app.kubernetes.io/managed-by": "Helm",
                           },
                           annotations= {
                                "eks.amazonaws.com/role-arn": role.role_arn,
                                "meta.helm.sh/release-name": "aws-mountpoint-s3-csi-driver", 
                                "meta.helm.sh/release-namespace": "kube-system", 
                           },
                           namespace="kube-system"
                        )
        
def EbsDriverServicea(self, cluster):
        conditions = CfnJson(self, 'ConditionJson',
          value = {
            "%s:aud" % cluster.cluster_open_id_connect_issuer : "sts.amazonaws.com",            # namespace # serviceaccountname
            "%s:sub" % cluster.cluster_open_id_connect_issuer : "system:serviceaccount:%s:%s" % ("kube-system","ebs-csi-controller-sa"),
          },
         )

        role =  iam.Role(self, "EbsDriverRole",
                          assumed_by=iam.OpenIdConnectPrincipal(cluster.open_id_connect_provider)
                                     .with_conditions({
                                        "StringEquals": conditions,
                                     }),
                                role_name="ebsdriverrole"
                        )
        
        statements = []
        with open(os.path.join(DIR, 'ebs_policy.json'), 'r') as f:
                data = json.load(f)
                for s in data['Statement']:
                    statements.append(iam.PolicyStatement.from_json(s))

        policy = iam.Policy(self, "ebsdriver",statements=statements, policy_name="ebsdriverpolicy")
        
        policy.attach_to_role(role)
        
        servicea = eks.ServiceAccount(self, 'ebs-csi-driver-sa',
                           cluster=cluster,
                           name="ebs-csi-controller-sa",
                           labels= {
                                "app.kubernetes.io/name": "ebs-csi-controller-sa",
                                "app.kubernetes.io/managed-by": "Helm",
                           },
                           annotations= {
                                "eks.amazonaws.com/role-arn": role.role_arn,
                                "meta.helm.sh/release-name": "aws-ebs-csi-driver", 
                                "meta.helm.sh/release-namespace": "kube-system", 
                           },
                           namespace="kube-system"
                        )

def EfsDriverServicea(self, cluster):
        conditions = CfnJson(self, 'ConditionJson',
          value = {
            "%s:aud" % cluster.cluster_open_id_connect_issuer : "sts.amazonaws.com",            # namespace # serviceaccountname
            "%s:sub" % cluster.cluster_open_id_connect_issuer : "system:serviceaccount:%s:%s" % ("kube-system","ebs-csi-controller-sa"),
          },
         )

        role =  iam.Role(self, "EfsDriverRole",
                          assumed_by=iam.OpenIdConnectPrincipal(cluster.open_id_connect_provider)
                                     .with_conditions({
                                        "StringEquals": conditions,
                                     }),
                                role_name="efsdriverrole"
                        )
        
        statements = []
        with open(os.path.join(DIR, 'efs_policy.json'), 'r') as f:
                data = json.load(f)
                for s in data['Statement']:
                    statements.append(iam.PolicyStatement.from_json(s))

        policy = iam.Policy(self, "efsdriver",statements=statements, policy_name="efsdriverpolicy")
        
        policy.attach_to_role(role)
        
        servicea = eks.ServiceAccount(self, 'efs-csi-driver-sa',
                           cluster=cluster,
                           name="efs-csi-controller-sa",
                           labels= {
                                "app.kubernetes.io/name": "efs-csi-controller-sa",
                                "app.kubernetes.io/managed-by": "Helm",
                           },
                           annotations= {
                                "eks.amazonaws.com/role-arn": role.role_arn,
                                "meta.helm.sh/release-name": "aws-efs-csi-driver", 
                                "meta.helm.sh/release-namespace": "kube-system", 
                           },
                           namespace="kube-system"
                        )



def AdotServiceAccount(self, cluster, namespacename, serviceaccountname)-> iam.IRole:
    conditions = CfnJson(self, 'ConditionJson',
                         value={
                             "%s:aud" % cluster.cluster_open_id_connect_issuer: "sts.amazonaws.com",
                             # namespace # serviceaccountname
                             "%s:sub" % cluster.cluster_open_id_connect_issuer: "system:serviceaccount:%s:%s" % (
                                 namespacename, serviceaccountname),
                         },
                         )

    role = iam.Role(self, "adotcollectorRole",
                    assumed_by=iam.OpenIdConnectPrincipal(cluster.open_id_connect_provider)
                    .with_conditions({
                        "StringEquals": conditions,
                    }),
                    role_name="adot-collector"
                    )
    role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name="AmazonPrometheusRemoteWriteAccess"))
    role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name="AWSXRayDaemonWriteAccess"))
    role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name="CloudWatchAgentServerPolicy"))

    namespace = eks.KubernetesManifest(
        self,
        "otel-namespace",
        cluster=cluster,
        manifest=[{
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {"name": namespacename}
        }]
    )

    eks.ServiceAccount(self, 'aws-otel-collector-sa',
                                  cluster=cluster,
                                  name=serviceaccountname,
                                  labels={
                                      "app.kubernetes.io/name": serviceaccountname
                                  },
                                  annotations={
                                      "eks.amazonaws.com/role-arn": role.role_arn,
                                  },
                                  namespace=namespacename
                                  )

    return role
    #servicea = eks.ServiceAccount(self, 'adot-collector-sa',
    #                   cluster=cluster,
    #                   name="adot-collector",
    #                   labels={
    #                       "app.kubernetes.io/name": "adot-collector",
    #                       "app.kubernetes.io/managed-by": "Helm",
    #                   },
    #                   annotations={
    #                       "eks.amazonaws.com/role-arn": role.role_arn,
    #                       "meta.helm.sh/release-name": "opentelemetry-collector",
    #                       "meta.helm.sh/release-namespace": "opentelemetry-collector",
    #                   },
    #                   namespace="opentelemetry-collector"
    #                   )
    # servicea.node.add_dependency(namespace)

def KedaServiceAccount(self, cluster, namespacename, serviceaccountname)-> iam.IRole:
    conditions = CfnJson(self, 'ConditionJson',
                         value={
                             "%s:aud" % cluster.cluster_open_id_connect_issuer: "sts.amazonaws.com",
                             # namespace # serviceaccountname
                             "%s:sub" % cluster.cluster_open_id_connect_issuer: "system:serviceaccount:%s:%s" % (
                                 namespacename, serviceaccountname),
                         },
                         )

    role = iam.Role(self, "kedaOperatorRole",
                    assumed_by=iam.OpenIdConnectPrincipal(cluster.open_id_connect_provider)
                    .with_conditions({
                        "StringEquals": conditions,
                    }),
                    role_name="keda-operator"
                    )
    role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name(managed_policy_name="AmazonPrometheusQueryAccess"))

    namespace = eks.KubernetesManifest(
        self,
        "keda-namespace",
        cluster=cluster,
        manifest=[{
            "apiVersion": "v1",
            "kind": "Namespace",
            "metadata": {"name": namespacename}
        }]
    )

    eks.ServiceAccount(self, 'keda-operator-sa',
                                  cluster=cluster,
                                  name=serviceaccountname,
                                  labels={
                                      "app.kubernetes.io/name": serviceaccountname,
                                      "app.kubernetes.io/managed-by": "Helm"
                                  },
                                  annotations={
                                      "eks.amazonaws.com/role-arn": role.role_arn,
                                      "meta.helm.sh/release-name": "keda",
                                      "meta.helm.sh/release-namespace": "keda",
                                  },
                                  namespace=namespacename
                                  )
    role.node.add_dependency(namespace)

    return role
    #servicea = eks.ServiceAccount(self, 'adot-collector-sa',
    #                   cluster=cluster,
    #                   name="adot-collector",
    #                   labels={
    #                       "app.kubernetes.io/name": "adot-collector",
    #                       "app.kubernetes.io/managed-by": "Helm",
    #                   },
    #                   annotations={
    #                       "eks.amazonaws.com/role-arn": role.role_arn,
    #                       "meta.helm.sh/release-name": "opentelemetry-collector",
    #                       "meta.helm.sh/release-namespace": "opentelemetry-collector",
    #                   },
    #                   namespace="opentelemetry-collector"
    #                   )
    # servicea.node.add_dependency(namespace)

def FluentBitSaRole(self, cluster, namespace, serviaccount, esdomain)-> iam.IRole:
    conditions = CfnJson(self, 'ConditionJson',
                         value={
                             "%s:aud" % cluster.cluster_open_id_connect_issuer: "sts.amazonaws.com",
                             # namespace # serviceaccountname
                             "%s:sub" % cluster.cluster_open_id_connect_issuer: "system:serviceaccount:%s:%s" % (
                                 namespace, serviaccount),
                         },
                         )

    role = iam.Role(self, "fluentbitrole",
                    assumed_by=iam.OpenIdConnectPrincipal(cluster.open_id_connect_provider)
                    .with_conditions({
                        "StringEquals": conditions,
                    }),
                    role_name="fluent-bit-role"
                    )
    policy = iam.Policy(self,
       "fluent-bit-policy",
        statements=[
            iam.PolicyStatement(
                    actions=["es:ESHttp*"],
                    effect=iam.Effect.ALLOW,
                    resources=[
                        f"arn:{Stack.of(self).partition}:es:{Stack.of(self).region}:{Stack.of(self).account}:domain/{esdomain}/*"]
                                          )
    ], policy_name="fluent-bit-policy")

    policy.attach_to_role(role)

    return role