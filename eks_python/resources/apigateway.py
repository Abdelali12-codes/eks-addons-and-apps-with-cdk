from aws_cdk import (Resource, CfnOutput)
from constructs import Construct
import aws_cdk.aws_apigateway as apg
import aws_cdk.aws_apigatewayv2 as apg2
from .route53 import Route53Record
import aws_cdk.aws_route53 as dns
import aws_cdk.aws_certificatemanager as certificate
import aws_cdk.aws_route53_targets as targets
from ..configuration.config import *



class ApiGateway(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope,id)


        # Rest Api
        restapi = apg.RestApi(self, "AWSApiGateway",
               deploy=True,
               endpoint_types=[apg.EndpointType.REGIONAL]
            )
        
        restapi.add_domain_name(
            "restapidmain",
            certificate=certificate.Certificate.from_certificate_arn(self, 
                    "AWSCertificateManager",
                     dnsconf['cert_arn']
                    ),
            domain_name=apigaetway['api_record_name']
        )
            
        # web socket

        # websocket = apg2.WebSocketApi(
        #     self,
        #     "",
        #     api_name=""
        # ) 
        
        # lamdauthorizer = apg.TokenAuthorizer(self, "AWSLambdaAuthorizer",
        #                 identity_source="method.request.header.Authorization",
        #                 handler=lambda_function,
        #                 authorizer_name="lambdaauthorizer",
        #                 results_cache_ttl=cdk.Duration.minutes(5)
        #             )
            
        # restapi.node.add_dependency(vpclink)
        #     #restapi.node.add_dependency(lambda_function) 
            
        app = restapi.root.add_resource("app")
        # v1  = app.add_resource("v1")
            
        methodreponse200 = apg.MethodResponse(
                status_code="200",
                response_models={
                    "application/json":apg.Model.EMPTY_MODEL
                }
            )
            
        methoderesponse300 = apg.MethodResponse(
                    status_code="300",
                    response_models={
                        "application/json":apg.Model.EMPTY_MODEL
                    }
                
                )
                
        methodreponse400 = apg.MethodResponse(
                status_code="400",
                response_models={
                    "application/json":apg.Model.EMPTY_MODEL
                }
            )
            
            
            
        integrationreponse = apg.IntegrationResponse(status_code="200",
                #response_parameters={
                #    "method.response.header.Status":"integration.response.header.Status"
               # },
                response_templates={
                    "application/json": "{ 'statusCode': 200 }"
                }
            )
        app.add_cors_preflight(
                allow_origins=["*"],
                allow_headers=apg.Cors.DEFAULT_HEADERS,
                allow_methods=apg.Cors.ALL_METHODS,
                status_code=204
            )
            
        app.add_method("GET",
                        integration=apg.Integration(
                            integration_http_method="GET",
                            type=apg.IntegrationType.HTTP_PROXY,
                            options=apg.IntegrationOptions(
                                integration_responses=[integrationreponse]
                            ),
                            uri=f"https://flaskappeks.abdelalitraining.com/app"
                        ),
                        # request_parameters={
                        #     "method.request.header.Authorization": True,
                        #     "method.request.querystring.file": True,
                        #     "method.request.querystring.data": True
                        # },
                        # authorizer=lamdauthorizer,
                        method_responses=[
                             methodreponse200,
                             methodreponse400,
                             methoderesponse300
                        ]
                )
                
        # api gatewau custom domain
        hostedzn = hostedzone(self)
        Route53Record(self, f"apigatewayrecord-${apigaetway['api_record_name'].split('.')[0]}", 
                        service= "apigateway",
                        record_name = apigaetway['api_record_name'],
                        hosted_zone = hostedzn,
                        target= dns.RecordTarget.from_alias(targets.ApiGateway(restapi)) 
                    )
        # v1.add_method("POST",
        #                 integration=apg.Integration(
        #                     integration_http_method="GET",
        #                     type=apg.IntegrationType.HTTP_PROXY,
        #                     options=apg.IntegrationOptions(
        #                         connection_type=apg.ConnectionType.VPC_LINK,
        #                         vpc_link=vpclink
        #                     ),
        #                     uri=f"http://{self.nlb.load_balancer_dns_name}:8080/app1"
        #                 ),
        #                 request_parameters={
        #                     "method.request.header.Authorization": True,
        #                     "method.request.querystring.file": True,
        #                     "method.request.querystring.data": True
        #                 },
        #                 authorizer=lamdauthorizer,
        #                 method_responses=[
        #                     methodreponse400
        #                 ]
        #         )
                