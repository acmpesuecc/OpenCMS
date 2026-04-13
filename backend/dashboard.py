from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List, Optional
from bson import ObjectId
from pathlib import Path
import os
from dotenv import load_dotenv

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

MONGO_URI = os.getenv("MONGO_URI")
client = AsyncIOMotorClient(MONGO_URI)
db = client["OpenCMS"]
project_collection = db["project"]

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

router = APIRouter()


class Project(BaseModel):
    name: str
    repo_link: str
    pages: List[str] = []  # list of post _ids



@router.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})


@router.get("/projects")
async def get_projects():
    try:
        result = await project_collection.find().to_list(100)
        for item in result:
            item["_id"] = str(item["_id"])
        return {"message": result}
    except Exception as e:
        return {"message": "Unsuccessful", "error": str(e)}


@router.get("/projects/{project_id}")
async def get_project(project_id: str):
    try:
        result = await project_collection.find_one({"_id": ObjectId(project_id)})
        return {"message": result}
    except Exception as e:
        return {"message": "Unsuccessful", "error": str(e)}


@router.post("/projects")
async def create_project(project: Project):
    try:
        post_data = project.model_dump()
        result = await project_collection.insert_one(post_data)
        return {"id": str(result.inserted_id), "message": "successful"}
    except Exception as e:
        return {"message": "Unsuccessful", "error": str(e)}


@router.patch("/projects/{project_id}/pages")
async def add_page(project_id: str, post_id: str):
    await project_collection.update_one(
        {"_id": ObjectId(project_id)},
        {"$push": {"pages": ObjectId(post_id)}}
    )
    return {"message": "Updated"}



@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    try:
        result = await project_collection.delete_one({"_id": ObjectId(project_id)})
        if result.deleted_count == 1:
            return {"message": "Post deleted successfully"}
        else:
            return {"message": "Post not found"}
    except Exception as e:
        return {"message": "Unsuccessful", "error": str(e)}



