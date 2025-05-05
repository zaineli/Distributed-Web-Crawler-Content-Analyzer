import os
import boto3
from dotenv import load_dotenv
import time
from crawlers import crawl_single_site

load_dotenv()

QUEUE_URL = os.getenv("SQS_QUEUE_URL")

sqs = boto3.client(
    'sqs',
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    region_name=os.getenv("AWS_DEFAULT_REGION"),
    )


def receive_and_process_messages():
    while True:
        response = sqs.receive_message(
            QueueUrl=QUEUE_URL,
            MaxNumberOfMessages=1,
            WaitTimeSeconds=20,
            VisibilityTimeout=10,
        )
    
        messages = response.get('Messages', [])
        if not messages:
            print("No messages to process.")
            time.sleep(5)  # Wait before checking again
            continue
        for message in messages:
            receipt_handle = message['ReceiptHandle']
            body = message['Body']
            print(f"Processing message: {body}")
            
            crawl_single_site(body)
    
            # Delete the message after processing
            sqs.delete_message(
                QueueUrl=QUEUE_URL,
                ReceiptHandle=receipt_handle
            )
            print(f"Deleted message: {body}")

receive_and_process_messages()