import aws_cdk.aws_iam as iam

def create_node_role(self):
        
        iam_role = iam.Role(self, "noderole", assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSWorkerNodePolicy"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKS_CNI_Policy"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2ContainerRegistryReadOnly"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
        iam_role.add_to_policy(iam.PolicyStatement(
            effect= iam.Effect.ALLOW,
            actions=["sts:AssumeRole"],
            resources=[ self.master_role.role_arn]
        ))
        return iam_role
    
def create_eks_role(self):
        
        iam_role = iam.Role(self, "eksrole", assumed_by=iam.ServicePrincipal("eks.amazonaws.com"))
        iam_role.add_managed_policy(iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEKSClusterPolicy"))
        
        return iam_role