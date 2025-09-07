import boto3
from botocore.exceptions import BotoCoreError, ClientError
import time

def list_s3_buckets():
    try:
        session = boto3.Session()
        s3 = session.client('s3')

        response = s3.list_buckets()
        print("✅ S3 Buckets:")
        for bucket in response['Buckets']:
            print(f" - {bucket['Name']}")

    except (BotoCoreError, ClientError) as error:
        print(f"❌ Error: {error}")

if __name__ == "__main__":
    list_s3_buckets()
    time.sleep(360)
