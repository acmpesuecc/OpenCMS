from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import RedirectResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
from authlib.integrations.starlette_client import OAuth
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List
from fastapi.templating import Jinja2Templates
from bson import ObjectId
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from pathlib import Path

# Explicitly load the .env file from the backend directory
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

from field_posts import router as router_fieldposts
from posts import router as router_posts
from images import router as router_images
from ssg_build import ssg_router

MONGO_URI = os.getenv("MONGO_URI")
SESSION_SECRET = os.getenv("SESSION_SECRET", "super-secret-key-123")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

client = AsyncIOMotorClient(MONGO_URI)
db = client["OpenCMS"]
collection_types = db["collection_types"]
components = db["components"]
users_collection = db["users"]

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))

pwd_context = CryptContext(
    schemes=["bcrypt_sha256"],
    default="bcrypt_sha256",
    deprecated=[]
)

oauth = OAuth()
if GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET:
    oauth.register(
        name="github",
        client_id=GITHUB_CLIENT_ID,
        client_secret=GITHUB_CLIENT_SECRET,
        access_token_url="https://github.com/login/oauth/access_token",
        authorize_url="https://github.com/login/oauth/authorize",
        api_base_url="https://api.github.com/",
        client_kwargs={"scope": "user:email"},
    )

from fastapi.staticfiles import StaticFiles

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

# Mount the static files so CSS can load correctly
try:
    app.mount("/static", StaticFiles(directory=str(Path(__file__).parent.parent / "frontend" / "static")), name="static")
except Exception as e:
    print("Static directory not found or error mounting:", e)

app.include_router(router_fieldposts)
app.include_router(router_posts)
app.include_router(router_images)
app.include_router(ssg_router)
from dashboard import router as dashboard_router
app.include_router(dashboard_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ComponentType(BaseModel):
    name: str
    type: str

class CollectionType(BaseModel):
    title: str
    components: List[str] = []  # array of component object id's

class UpdateComponents(BaseModel):
    components: List[str] = []  # list of component IDs to set

class LoginRequest(BaseModel):
    email: str
    password: str

class SignupRequest(BaseModel):
    username: str
    email: str
    password: str


@app.get("/fieldtypes")
async def root(request: Request):
    return templates.TemplateResponse("collection_types.html", {"request": request})

@app.get("/addpost")
async def addpost(request: Request):
    return templates.TemplateResponse("addpost.html", {"request": request})

@app.get("/login")
async def login_page():
    return FileResponse(str(Path(__file__).parent.parent / "frontend" / "templates" / "login.html"))

@app.post("/login")
async def login(data: LoginRequest):
    user = await users_collection.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not pwd_context.verify(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": "Login successful"}

@app.get("/signup")
async def signup_page():
    return FileResponse(str(Path(__file__).parent.parent / "frontend" / "templates" / "signup.html"))

@app.post("/signup")
async def signup(data: SignupRequest):
    existing_user = await users_collection.find_one({"email": data.email})

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = pwd_context.hash(data.password)

    await users_collection.insert_one({
        "username": data.username,
        "email": data.email,
        "password": hashed_password
    })

    return {"message": "User created successfully"}

@app.get("/login/github")
async def login_github(request: Request):
    if not oauth.github:
        raise HTTPException(status_code=500, detail="GitHub OAuth not configured properly in .env")
        
    redirect_uri = str(request.url_for("github_callback"))
    return await oauth.github.authorize_redirect(request, redirect_uri)

@app.get("/auth/github/callback")
async def github_callback(request: Request):
    try:
        token = await oauth.github.authorize_access_token(request)
        resp = await oauth.github.get("user", token=token)
        user = resp.json()
        request.session["user"] = user
        return RedirectResponse("/dashboard")
    except Exception as e:
        return {"error": str(e)}

@app.get("/dashboard")
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.post("/fieldtypes")
async def func(collection_type: CollectionType):

    try:
        data=collection_type.model_dump()
        result= await collection_types.insert_one(data)
        return {"id": str(result.inserted_id)}
    except Exception as e:
        return {"message":"Unsuccessful","error": e}

@app.get("/get-components")
async def func():
    try:
        result= await components.find().to_list(100)
        for item in result:
            item["_id"] = str(item["_id"])
        return {"message": result}
    except Exception as e:
        return {"message":"Unsuccessful","error": e}

@app.get("/get-components/{componentId}")
async def func(componentId:str):
    try:
        result= await components.find_one({"_id":ObjectId(componentId)})
        if result:
            result["_id"] = str(result["_id"])
        return {"message": result}
    except Exception as e:
        return {"message":"Unsuccessful","error": e}

@app.get("/field-types/")
async def getfield():
    result= await collection_types.find().to_list(100)
    for item in result:
        item["_id"] = str(item["_id"])
    return {"field": result}


@app.get("/fieldtypes/{fieldId}")
async def getfield(fieldId:str):
    result= await collection_types.find_one({"_id":ObjectId(fieldId)})
    if result:
        result["_id"] = str(result["_id"])
    return {"field": result}

@app.patch("/fieldtypes/{fieldId}")
async def updatefield(fieldId:str, data: UpdateComponents):
    await collection_types.update_one(
        {"_id": ObjectId(fieldId)},
        {"$set": {"components": [ObjectId(c) for c in data.components]}}
    )
    return {"message": "Updated"}
