from aws_cdk import (Resource, CfnOutput, RemovalPolicy, Duration)
import aws_cdk.aws_cognito as cognito
from ..configuration.config import *



class Cognito(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope,id)
        
        self.userPool = cognito.UserPool(self,f"{id}-CognitoUserPool", 
            user_pool_name = cognitoconf["userpoolname"],
            removal_policy = RemovalPolicy.DESTROY
        )
        
        self.userPool.add_client(
            "UserPoolAppClient",
            user_pool_client_name= cognitoconf["appclient_name"],
            access_token_validity = Duration.days(1),
            id_token_validity = Duration.days(1),
            generate_secret = True,
            auth_flows = cognito.AuthFlow(
              admin_user_password = False,
              custom = True,
              user_password = False
            ),
            o_auth = cognito.OAuthSettings(
                flows = cognito.OAuthFlows(
                    authorization_code_grant =True,
                    implicit_code_grant = False,
                    client_credentials = False
                )
            ),
        )
        
        domain = cognito.UserPoolDomain(self,"CognitoUserPoolDomain", 
           user_pool = self.userPool,
           cognito_domain = cognito.CognitoDomainOptions(
                domain_prefix=cognitoconf["domain-prefix"]
            )
        )

        self.domain_name = domain.domain_name
        
        
        CfnOutput(self, "domainname", value=domain.domain_name)