import json
import boto3

def handler(event, context):
    try:
        if 'BucketName' in event:
            bucket = event['BucketName']
            s3 = boto3.resource('s3')
            bucket = s3.Bucket(bucket)
            for obj in bucket.objects.filter():
                s3.Object(bucket.name, obj.key).delete()
    except Exception as e:
        print(e)

