from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Union
from crawlers import crawl_single_site, batch_crawl_multiple_sites
from fastapi.middleware.cors import CORSMiddleware
import boto3
import os

app = FastAPI()

# Request model
class URLRequest(BaseModel):
    urls: Union[str, List[str]]  # Accept a single URL or list of URLs

sqs = boto3.client('sqs', region_name=os.getenv("AWS_DEFAULT_REGION"))

QUEUE_URL = os.getenv("SQS_QUEUE_URL")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # or ["*"] for testing only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def send_urls_to_queue(url_list):
    for url in url_list:
        response = sqs.send_message(
            QueueUrl=QUEUE_URL,
            MessageBody=url
        )
        print(f"Sent: {url} | MessageId: {response['MessageId']}")

# POST endpoint
@app.post("/crawl/")
async def crawl(request: URLRequest):
    try:
        if isinstance(request.urls, str):
            result = crawl_single_site(request.urls)
        else:
            result = batch_crawl_multiple_sites(request.urls)
        return {"results": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/submit-url")
async def submit_url(request: URLRequest):
    if not request.urls:
        return {"error": "URL not provided"}

    try:
        if isinstance(request.urls, str):
            url_list = [request.urls]
        else:
            url_list = request.urls

        # Send URLs to SQS
        send_urls_to_queue(url_list)

        return {"message": "URLs submitted successfully", "urls": url_list}
        
    except Exception as e:
        return {"error": str(e)}