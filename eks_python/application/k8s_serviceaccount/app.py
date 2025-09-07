import boto3
from botocore.exceptions import BotoCoreError, ClientError
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def list_s3_buckets():
    try:
        session = boto3.Session()
        s3 = session.client('s3')

        response = s3.list_buckets()
        logging.info("✅ S3 Buckets:")
        for bucket in response['Buckets']:
            logging.info(f" - {bucket['Name']}")

    except (BotoCoreError, ClientError) as error:
        logging.error(f"❌ Error: {error}")

if __name__ == "__main__":
    list_s3_buckets()
    time.sleep(3600)  # Sleep to keep script running
