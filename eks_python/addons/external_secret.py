from aws_cdk import (Resource, Stack, RemovalPolicy)
import aws_cdk.aws_eks as eks
import aws_cdk.aws_ecr as ecr
import aws_cdk.aws_iam as iam
import aws_cdk.custom_resources as custom
from cdk_ecr_deployment import (ECRDeployment, DockerImageName)
from ..policies.main import ExternalSecretServiceAccount


class ExternalSecret(Resource):
    def __init__(self, scope, id , **kwargs):
        super().__init__(scope, id)
        
        cluster = None 
        if 'cluster' in kwargs:
            cluster = kwargs['cluster']
        else:
            raise Exception("you should provide the cluster arg")
        

        ExternalSecretServiceAccount(self, cluster=cluster)
        ecr_repo = ecr.Repository(self, "EcrExternalSecret", 
                                    repository_name="external-secrets",
                                    empty_on_delete=True,
                                    removal_policy=RemovalPolicy.DESTROY
                                )
        lambda_role = iam.Role(self, "deletecrexternalsecretlambdarole",assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"))
        policy = iam.Policy(self, "deletecrexternalsecretlambdapolicy",
          statements=[iam.PolicyStatement(
            actions=["ecr:*", "elasticloadbalancing:*", "lambda:*", "secretsmanager:*", "logs:CreateLogGroup",
                                            "logs:CreateLogStream",
                                            "logs:PutLogEvents"],
            resources=["*"],
            effect=iam.Effect.ALLOW
        )])

        policy.attach_to_role(lambda_role)

        delete_ecr = custom.AwsCustomResource(self, "deletecrexternalsecret", on_delete=custom.AwsSdkCall(
            action="DeleteRepository",
            parameters={
              "force": True,
              "repositoryName": ecr_repo.repository_name
            },
            service="ECR",

        ), role=lambda_role)

        delete_ecr.node.add_dependency(ecr_repo)
        
        ECRDeployment(self, "externalsecretECR", 
                        src= DockerImageName("ghcr.io/external-secrets/external-secrets:v0.9.13"),
                        dest= DockerImageName(f"{ecr_repo.repository_uri}:v0.9.13")
                    )
        externalsecret = eks.HelmChart(self, "externalsecrethelm",
                      cluster= cluster,
                      namespace= "external-secret",
                      repository="https://charts.external-secrets.io",
                      release="external-secrets",
                      wait=True,
                      chart="external-secrets",
                      values= {
                          "image":{
                             "repository": ecr_repo.repository_uri,
                             "tag": "v0.9.13"
                          },
                          "webhook":{
                              "port": 9443 ,  
                              "image": {
                                  "repository": ecr_repo.repository_uri,
                                  "tag": "v0.9.13"
                              }
                          },
                          "certController":{
                              "image":{
                                   "repository": ecr_repo.repository_uri,
                                  "tag": "v0.9.13"
                              }
                          },
                           "extraEnv":[
                               {
                                   "name": "AWS_SECRETSMANAGER_ENDPOINT", 
                                   "value": "https://secretsmanager.%s.amazonaws.com" % Stack.of(self).region
                               },
                               {
                                   "name": "AWS_STS_ENDPOINT", 
                                   "value": "https://sts.%s.amazonaws.com" % Stack.of(self).region
                               },
                               {
                                   "name": "AWS_SSM_ENDPOINT",
                                   "value": "https://ssm.%s.amazonaws.com" % Stack.of(self).region
                               }
                           ]
                          
                      }
                    )
        
        clustersecretstore= eks.KubernetesManifest(self, "ClusterSecretStore",
                              cluster= cluster,
                              manifest=[{
                                "apiVersion": "external-secrets.io/v1beta1",
                                "kind": "ClusterSecretStore",
                                "metadata":{
                                    "name": "cluster-secret-store"
                                },
                                "spec":{
                                    "provider": {
                                        "aws": {
                                            "service": "SecretsManager",
                                            "region": Stack.of(self).region,
                                            "auth": {
                                                "jwt": {
                                                    "serviceAccountRef": {
                                                        "name": "external-secret-sa",
                                                        "namespace": "external-secret"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }

                              }]
                            )
        clustersecretstore.node.add_dependency(externalsecret)
