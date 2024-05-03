from aws_cdk import (Resource, CfnDynamicReference,Fn, Stack, CfnDynamicReferenceService)
from jinja2 import Environment, FileSystemLoader
import aws_cdk.aws_secretsmanager as secret
from ..configuration.config import dnsconf, rdsdb, opensearch
from ..policies.main import lambdaRole
import aws_cdk.custom_resources as custom
import aws_cdk.aws_route53 as dns 
import aws_cdk.aws_route53_targets as targets
import aws_cdk.aws_elasticloadbalancingv2 as elbv2
from ..configuration.config import hostedzone
from ..resources.route53 import Route53Record
import os
import json
import glob
import yaml

DIR = os.path.dirname(os.path.realpath(__file__))


class Applications(Resource):
    def __init__(self, scope, id, externalsecret, db_secret, cluster, ingress, vpc,
                  db_host, es_domain, cognito_domain, eksprofile, **kwargs):
        super().__init__(scope, id)
        count = 0
        for item in glob.glob(os.path.join(DIR, '*.yaml')):
            file = os.path.basename(item)
            with open(os.path.join(DIR, file)) as content:
                configuration = yaml.safe_load(content)
                if configuration['deploy'].lower() == 'true':
                    if 'secretname' in configuration:
                    # create secret
                        external = cluster.add_manifest(f'{file.split('.')[0]}-externalsecret',{
                            "apiVersion": "external-secrets.io/v1beta1",
                            "kind": "ExternalSecret",
                            "metadata":{
                                "name": configuration['manifest']['metadata']['name'],
                                "namespace": configuration['manifest']['metadata']['namespace']
                            },
                            "spec":{
                                "refreshInterval": "1h",
                                "secretStoreRef": {
                                    "name": "cluster-secret-store",
                                    "kind": "ClusterSecretStore"
                                },
                                "target":{
                                    "name": configuration['manifest']['metadata']['name'],
                                    "creationPolicy": "Owner"
                                },
                                "data": [
                                   {
                                       "secretKey": "DB_USERNAME",
                                       "remoteRef": {
                                           "key": rdsdb['secretname'],
                                           "property": "username"
                                       }
                                   },
                                   {
                                       "secretKey": "DB_PASSWORD",
                                       "remoteRef": {
                                           "key": rdsdb['secretname'],
                                           "property": "password"
                                       }
                                   },
                                   {
                                       "secretKey": "ES_USERNAME",
                                       "remoteRef": {
                                           "key": opensearch['secretname'],
                                           "property": "username"
                                       }
                                   },
                                   {
                                       "secretKey": "ES_PASSWORD",
                                       "remoteRef": {
                                           "key": opensearch['secretname'],
                                           "property": "password"
                                       }
                                   }
                                ]
                                # ],
                                # "dataFrom":[
                                #    {
                                #        "extract":{
                                #                 "key": configuration['secretname']
                                #        }
                                #    }
                                # ]
        
                            }
                        })
                        external.node.add_dependency(externalsecret)
                        # modify the env of deployment
                        configuration['manifest']['spec']['template']['spec']['containers'][0]['envFrom'] = [
                            {
                                "secretRef": {
                                    "name": configuration['manifest']['metadata']['name']
                                }
                            }
                        ]
                    
                    # add db env
                    # configuration['manifest']['spec']['template']['spec']['containers'][0]['env'] = [
                    #     {
                    #         "name": "DB_HOST",
                    #         "value": db_host
                    #     },
                    #     {
                    #         "name": "ES_HOST",
                    #         "value": es_domain
                    #     },
                    #     {
                    #         "name": "COGNITO_DOMAIN",
                    #         "value": f"{cognito_domain}.auth.{Stack.of(self).region}.amazoncognito.com"
                    #     }
                    # ]
                    # deployment
                    cluster.add_manifest(f'{file.split('.')[0]}-deployment-manifest', configuration['manifest'])
                    # service
                    cluster.add_manifest(f'{file.split('.')[0]}-service-manifest', {
                            'apiVersion': 'v1',
                            'kind': 'Service', 
                            'metadata': {
                                'name': configuration['manifest']['metadata']['name']
                            }, 
                            'spec': {
                            'type': 'ClusterIP',
                            'selector': configuration['manifest']['spec']['template']['metadata']['labels'], 
                            'ports': [{'port': configuration['manifest']['spec']['template']['spec']['containers'][0]['ports'][0]['containerPort'], 
                                        'targetPort': configuration['manifest']['spec']['template']['spec']['containers'][0]['ports'][0]['containerPort']}]
                            }
                            })

                # deploy ingress for application
                
                env = Environment(loader=FileSystemLoader(DIR))
                template = env.get_template('ingress.yaml.j2')

                if  'ingress' in configuration:
                    if configuration['ingress']['deploy'] == "true":
                        rendered_template = template.render({
                            "name": configuration['manifest']['metadata']['name'],
                            "healthcheckpath": configuration['ingress']['healthcheckpath'],
                            "grouporder": count +2,
                            "certificatearn": dnsconf['cert_arn'],
                            "domain": dnsconf['domain'],
                            "hosts": configuration['ingress']['hosts'],
                            "path": configuration['ingress']['path'],
                            "service": configuration['manifest']['metadata']['name'],
                            "port": configuration['manifest']['spec']['template']['spec']['containers'][0]['ports'][0]['containerPort']
                        })

                        manifest = yaml.safe_load(rendered_template)
                        ingressmanifest = cluster.add_manifest(f'{configuration['manifest']['metadata']['name']}-{manifest['kind'].lower()}-manifest-{count+1}', manifest)
                        ingressmanifest.node.add_dependency(ingress)
                        ingressmanifest.node.add_dependency(cluster)
                        ingressmanifest.node.add_dependency(vpc)
                        ingressmanifest.node.add_dependency(eksprofile)

                        # once ingress is created, create dns record
                        # lamnda_role = lambdaRole(self, "elbdescribe")
                        # elbdescribe = custom.AwsCustomResource(self, f'customresource-{id}',
                        #         on_create=custom.AwsSdkCall(
                        #         action="DescribeLoadBalancers",
                        #         service="elastic-load-balancing-v2",
                        #         parameters={
                        #             "Names": [ 
                        #                             manifest['metadata']['annotations']['alb.ingress.kubernetes.io/load-balancer-name'],
                        #                         ]
                        #         },
                        #         physical_resource_id= custom.PhysicalResourceId.of("ELB-AwsCustomResource")

                        #     ),
                        #     role=lamnda_role     
                        # )

                        # elbdescribe.node.add_dependency(ingressmanifest)

                        # elbdns = elbdescribe.get_response_field('LoadBalancers.0.DNSName')
                        # elbarn= elbdescribe.get_response_field('LoadBalancers.0.LoadBalancerArn')
                        # CanonicalHostedZoneId = elbdescribe.get_response_field('LoadBalancers.0.CanonicalHostedZoneId')
                        # securitygroup = elbdescribe.get_response_field('LoadBalancers.0.SecurityGroups.0')
                        
                        # elbtarget = elbv2.ApplicationLoadBalancer.from_application_load_balancer_attributes(self,"ingresselb",
                        #                                load_balancer_arn=elbarn,
                        #                                load_balancer_dns_name=elbdns,
                        #                                 load_balancer_canonical_hosted_zone_id=CanonicalHostedZoneId,
                        #                                 security_group_id= securitygroup                                         
                        #                              )

                        # elbtarget.node.add_dependency(ingressmanifest)

                        # hostedzn = hostedzone(self)
                        # for host in configuration['ingress']['hosts']:

                        #     record = Route53Record(self, f"applicationrecord-${host.split('.')[0]}", 
                        #                     service= "ingress",
                        #                     record_name = host,
                        #                     hosted_zone = hostedzn,
                        #                     target= dns.RecordTarget.from_alias(targets.LoadBalancerTarget(elbtarget)) 
                        #                 )
                        #     record.node.add_dependency(ingressmanifest)

                count = count +1
 

        
        

