from fastapi import APIRouter
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from typing import List, Optional
from bson import ObjectId
from datetime import datetime
import os
from pathlib import Path
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

router = APIRouter()

MONGO_URI = os.getenv("MONGO_URI")  
client = AsyncIOMotorClient(MONGO_URI)
db = client["OpenCMS"]
posts_collection = db["posts"]

class Post(BaseModel):
    projectId: Optional[str] = None
    title: str
    content: str
    excerpt: Optional[str] = None
    status: str = "draft"
    tags: list[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    user_id: Optional[int] = None  

@router.post("/posts")
async def save(post: Post):
    try:
        post_dict = post.model_dump()
        result = await posts_collection.insert_one(post_dict)
        return {"id": str(result.inserted_id), "message": "successful"}
    except Exception as e:
        return {"message": "Unsuccessful", "error": str(e)}

@router.get("/posts")
async def getposts():
    try:
        result = await posts_collection.find().to_list(100)
        for post in result:
            post['_id'] = str(post['_id'])
        return result
    except Exception as e:
        return {"message": "Unsuccessful", "error": str(e)}

@router.delete("/posts/{postId}")
async def deletepost(postId: str):
    try:
        result = await posts_collection.delete_one({"_id": ObjectId(postId)})
        if result.deleted_count == 1:
            return {"message": "Post deleted successfully"}
        else:
            return {"message": "Post not found"}
    except Exception as e:
        return {"message": "Unsuccessful", "error": str(e)}


@router.put("/posts/{postId}")
async def updatepost(postId: str, post: Post):
    try:
        post_dict = post.model_dump()
        result = await posts_collection.update_one(
            {"_id": ObjectId(postId)},
            {"$set": post_dict}
        )
        if result.modified_count == 1:
            return {"message": "Post updated successfully"}
        else:
            return {"message": "Post not found or no changes made"}
    except Exception as e:
        return {"message": "Unsuccessful", "error": str(e)}
