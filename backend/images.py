from fastapi import FastAPI, UploadFile, File
import os
from dotenv import load_dotenv
import boto3
from fastapi import APIRouter

router = APIRouter()

load_dotenv()

# THESE ALL WILL BE UPDATED LATER:

R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")

from botocore.client import Config

s3_client = boto3.client(
    "s3",
    endpoint_url=R2_ENDPOINT_URL,
    aws_access_key_id=R2_ACCESS_KEY,
    aws_secret_access_key=R2_SECRET_KEY,
    config=Config(signature_version='s3v4')
)


@router.post('/upload/')
async def upload(file: UploadFile = File(...)):
    try:

        file_contents = await file.read()
        
        s3_client.put_object(
            Bucket=R2_BUCKET_NAME,
            Key=file.filename,
            Body=file_contents,
            ContentType=file.content_type
        )
        
        return {"message": f"Successfully uploaded {file.filename}", "filename": file.filename}
    except Exception as e:
        return {"error": str(e)}

@router.get('/image-url/{filename}')
async def get_image_url(filename: str):
    # Generates a temporary, secure URL to view an image from a private bucket
    try:
        presigned_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': R2_BUCKET_NAME,
                'Key': filename
            },
            ExpiresIn=3600 # i set a temporary expiry time of 1 hour
        )
        return {"url": presigned_url}
    except Exception as e:
        return {"error": str(e)}
