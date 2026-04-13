from fastapi import APIRouter, HTTPException
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from bson import ObjectId
import os
import base64
import httpx
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv("MONGO_URI")
GITHUB_TOKEN = os.getenv("ACCESS_TOKEN")

db_client = AsyncIOMotorClient(MONGO_URI)
db = db_client["OpenCMS"]

ssg_router = APIRouter(prefix="/ssg", tags=["ssg"])


async def commit_to_github(repo: str, file_path: str, content: str, commit_message: str):
    url = f"https://api.github.com/repos/{repo}/contents/{file_path}"
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    encoded_content = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    async with httpx.AsyncClient() as client:
        # Check if file already exists (need its SHA to update)
        get_resp = await client.get(url, headers=headers)
        sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None

        payload = {
            "message": commit_message,
            "content": encoded_content,
        }
        if sha:
            payload["sha"] = sha  # required when updating an existing file

        put_resp = await client.put(url, headers=headers, json=payload)

    if put_resp.status_code not in (200, 201):
        error_msg = put_resp.json()
        if put_resp.status_code == 404:
            raise HTTPException(
                status_code=404,
                detail=f"GitHub returned 404 Not Found. Make sure the repo '{repo}' exists,. your token has 'Contents: Read and write' permissions, and you can access the repository."
            )
        elif put_resp.status_code == 401 or put_resp.status_code == 403:
            raise HTTPException(
                status_code=403,
                detail=f"GitHub permission denied (403/401). Your token is likely invalid, expired, or doesn't have write access to '{repo}'."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"GitHub commit failed with status {put_resp.status_code}: {error_msg}"
            )

    return put_resp.json()


@ssg_router.post("/publish/{post_id}")
async def publish_post(post_id: str):
    # 1. Fetch post
    post = await db["field_posts"].find_one({"_id": ObjectId(post_id)})
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")

    # 2. Fetch linked project (for repo_link)
    project = await db["project"].find_one({"_id": ObjectId(post["projectId"])})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # repo_link is like "https://github.com/user/repo"
    repo = project["repo_link"].replace("https://github.com/", "").rstrip("/")

    # 3. Build markdown content
    title = post.get("title", "untitled")
    is_draft = post.get("status", "draft") != "published"
    body_parts = []
    
    import boto3
    from botocore.client import Config
    
    # We will instantiate S3 client if needed
    R2_ACCESS_KEY = os.getenv("R2_ACCESS_KEY")
    R2_SECRET_KEY = os.getenv("R2_SECRET_KEY")
    R2_BUCKET_NAME = os.getenv("R2_BUCKET_NAME")
    R2_ENDPOINT_URL = os.getenv("R2_ENDPOINT_URL")

    s3_client = None
    if R2_ACCESS_KEY:
        s3_client = boto3.client(
            "s3",
            endpoint_url=R2_ENDPOINT_URL,
            aws_access_key_id=R2_ACCESS_KEY,
            aws_secret_access_key=R2_SECRET_KEY,
            config=Config(signature_version='s3v4')
        )

    for comp in post.get("components", []):
        content = comp.get("content")
        if not content:
            continue
            
        comp_doc = await db["components"].find_one({"_id": ObjectId(comp["componentId"])})
        
        # If it's a file component, fetch image from S3, upload to GitHub, and return markdown image tag
        if comp_doc and comp_doc.get("type") == "file":
            # Content could be multiple files like "image1.jpg,image2.png"
            file_names = content.split(",")
            resolved_images = []
            for filename in file_names:
                filename = filename.strip()
                if not filename:
                    continue
                    
                static_path = f"static/images/{filename}"
                hugo_path = f"/images/{filename}"
                
                # Fetch original file binary from S3
                if s3_client:
                    try:
                        s3_resp = s3_client.get_object(Bucket=R2_BUCKET_NAME, Key=filename)
                        binary_content = s3_resp['Body'].read()
                        
                        # Upload binary string directly to GitHub
                        url = f"https://api.github.com/repos/{repo}/contents/{static_path}"
                        headers = {
                            "Authorization": f"Bearer {GITHUB_TOKEN}",
                            "Accept": "application/vnd.github+json"
                        }
                        
                        async with httpx.AsyncClient() as client:
                            get_resp = await client.get(url, headers=headers)
                            sha = get_resp.json().get("sha") if get_resp.status_code == 200 else None
                            
                            payload = {
                                "message": f"cms: upload image {filename}",
                                "content": base64.b64encode(binary_content).decode("utf-8"),
                            }
                            if sha:
                                payload["sha"] = sha
                                
                            await client.put(url, headers=headers, json=payload)
                            
                        resolved_images.append(f"![Image]({hugo_path})")
                    except Exception as e:
                        print(f"Failed to migrate S3 image {filename} to GitHub: {e}")
                        resolved_images.append(f"<!-- Failed to load image {filename} -->")
                else:
                    resolved_images.append(f"![Image]({hugo_path})")
            
            body_parts.append("\n\n".join(resolved_images))
        else:
            body_parts.append(content)

    body = "\n\n".join(body_parts)

    markdown = f"""---
title: "{title}"
draft: {"true" if is_draft else "false"}
---

{body}
"""

    # 4. Commit to GitHub repo
    slug = title.lower().replace(" ", "-").replace("/", "-")
    file_path = f"content/{slug}.md"

    result = await commit_to_github(
        repo=repo,
        file_path=file_path,
        content=markdown,
        commit_message=f"cms: publish '{title}'"
    )

    return {
        "post": title,
        "repo": repo,
        "file": file_path,
        "commit": result.get("commit", {}).get("sha", "unknown")
    }
