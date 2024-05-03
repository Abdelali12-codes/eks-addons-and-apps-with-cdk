import json
import boto3
import time

elb = boto3.client('elbv2')

def handler(event, context):
    noexist = True
    start_time = time.time()
    while noexist:
            try:
                if 'ELBName' in event:
                    loadbalancername = event['ELBName']
                    response = elb.describe_load_balancers(
                            Names=[
                                    loadbalancername
                                ],
                        )
                    
                    threshold = time.time() - start_time
                    threshold = threshold / 60
                    if threshold > 10:
                         return {
                                "statusCode": 500,
                                "body": "Insufficient remaining time to complete the operation."
                            }
                    else:
                        if 'LoadBalancers' not in response:
                            time.sleep(120)
                        else:
                            return response
                    # if 'LoadBalancers' in load_balancers:
                    #     if len(load_balancers['LoadBalancers']) > 0:
                    #         loadbalancer_arn = load_balancers['LoadBalancers'][0]['LoadBalancerArn']

                    #         reponse = elb.delete_load_balancer(
                    #                             LoadBalancerArn=loadbalancer_arn
                    #                         )
                    #         if 'LoadBalancers' in load_balancers:
                    #             if len(load_balancers['SecurityGroups']) > 0:
                    #                 for sg in load_balancers['SecurityGroups']:
                    #                         ec2.delete_security_group(
                    #                             GroupId=sg
                    #                         )
                
            except Exception as e:
                print(e)


