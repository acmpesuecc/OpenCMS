from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List
from fastapi.templating import Jinja2Templates
from bson import ObjectId
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi import APIRouter

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)



MONGO_URI = os.getenv("MONGO_URI")

client = AsyncIOMotorClient(MONGO_URI)
db = client["OpenCMS"]  
field_posts = db["field_posts"]
components = db["components"]

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

router = APIRouter()

class ComponentType(BaseModel):
    name: str
    type: str

class CollectionType(BaseModel):
    title: str
    components: List[str] = []  

class ComponentItem(BaseModel):
    componentId: str
    content: str

class FieldContent(BaseModel):
    projectId: str
    fieldId: str
    title: str
    status: str
    components: List[ComponentItem] = []


@router.get("/editor")
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@router.get("/fieldposts/")
async def get():
    try:
        result = await field_posts.find().to_list(100)
        for item in result:
            item["_id"] = str(item["_id"])
        return {"message": result}
    except Exception as e:
        return {"message": "Unsuccessful", "error": str(e)}
    

@router.get("/fieldposts/{postId}")
async def get(postId:str):
    try:
        result = await field_posts.find_one({"_id":ObjectId(postId)})
        return {"message": result}
    except Exception as e:
        return {"message": "Unsuccessful", "error": str(e)}
    

@router.post("/fieldposts/")
async def create(field_content: FieldContent):
    try:
        post_data = field_content.model_dump()
        result = await field_posts.insert_one(post_data)
        return {"id": str(result.inserted_id), "message": "successful"}
    except Exception as e:
        return {"message": "Unsuccessful", "error": str(e)}

@router.put("/fieldposts/{postId}")
async def updatepost(postId: str,field_content: FieldContent):
    try:
        post_data = field_content.model_dump()
        result = await field_posts.update_one(
            {"_id": ObjectId(postId)},
            {"$set": post_data}
        )
        if result.modified_count == 1:
            return {"message": "Post updated successfully"}
        else:
            return {"message": "Post not found or no changes made"}
    except Exception as e:
        return {"message": "Unsuccessful", "error": str(e)}
    
@router.delete("/fieldposts/{postId}")
async def deletepost(postId: str):
    try:
        result = await field_posts.delete_one({"_id": ObjectId(postId)})
        if result.deleted_count == 1:
            return {"message": "Post deleted successfully"}
        else:
            return {"message": "Post not found"}
    except Exception as e:
        return {"message": "Unsuccessful", "error": str(e)}


