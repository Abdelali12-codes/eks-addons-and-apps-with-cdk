from aws_cdk import (Resource, CfnOutput, RemovalPolicy)
import aws_cdk.aws_cloudfront as cloudfront
import aws_cdk.aws_cloudfront_origins as origins
import aws_cdk.aws_s3 as s3
import aws_cdk.aws_certificatemanager as certificate
import aws_cdk.aws_route53 as dns
import aws_cdk.aws_route53_targets as targets
from .route53 import Route53Record
from ..configuration.config import *


class Cloudfront(Resource):
    def __init__(self, scope, id, **kwargs):
        super().__init__(scope,id)

    
        bucket = s3.Bucket(self,"cloudfrontbucket", 
                           bucket_name=cldfront['bucket_name'], removal_policy=RemovalPolicy.DESTROY)
        

        # originacess = cloudfront.OriginAccessIdentity(self, 'cloudfrontorigin')
        # bucket.grant_read(originacess)
        
        distribution = cloudfront.Distribution(self, "AwsCloudfrontDistribution",
                default_behavior=cloudfront.BehaviorOptions(
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                    origin_request_policy=cloudfront.OriginRequestPolicy(
                        self,"cloudfrontOriginRequestPolicy",
                        header_behavior=cloudfront.OriginRequestHeaderBehavior.allow_list("Accept-Language","CloudFront-Forwarded-Proto"),
                        query_string_behavior=cloudfront.OriginRequestQueryStringBehavior.allow_list("name")
                    ),
                    cache_policy=cloudfront.CachePolicy(self, "cloudfrontcachepolicy",
                       cache_policy_name="cloudfrontcachepolicys3",
                       header_behavior=cloudfront.CacheHeaderBehavior.allow_list("Authorization")
                    ),
                    origin=origins.S3Origin(
                        bucket=bucket,
                    )
                ),
                error_responses=[
                    cloudfront.ErrorResponse(
                        http_status=403,
                        response_page_path="/index.html",
                        response_http_status=200
                    ),
                    cloudfront.ErrorResponse(
                        http_status=404,
                        response_page_path="/index.html",
                        response_http_status=200
                    )
                ],
                certificate=certificate.Certificate.from_certificate_arn(self, 
                    "AWSCertificateManager",
                     dnsconf['cert_arn_us_east_1']
                    ),
                domain_names=cldfront['record_names'],
                
        )
         
        hostedzn = hostedzone(self)
        # create dns record
        for record in cldfront['record_names']:    
            Route53Record(self, f"cloudfrontrecord-${record.split('.')[0]}", 
                        service= "cloudfront",
                        record_name = record,
                        hosted_zone = hostedzn,
                        target= dns.RecordTarget.from_alias(targets.CloudFrontTarget(distribution)) 
                    )
        #
        CfnOutput(self, 'cloudfrontdistributionid', value=distribution.distribution_id)