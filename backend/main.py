import os
from typing import List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pymongo import MongoClient
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

MONGO_URI = os.getenv("MONGO_URI")
DATABASE_NAME = os.getenv("DATABASE_NAME")
SESSION_SECRET = os.getenv("SESSION_SECRET")
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

app.add_middleware(SessionMiddleware, secret_key=SESSION_SECRET)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth = OAuth()

oauth.register(
    name="github",
    client_id=GITHUB_CLIENT_ID,
    client_secret=GITHUB_CLIENT_SECRET,
    access_token_url="https://github.com/login/oauth/access_token",
    authorize_url="https://github.com/login/oauth/authorize",
    api_base_url="https://api.github.com/",
    client_kwargs={"scope": "user:email"},
)

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]
users_collection = db["users"]

pwd_context = CryptContext(
    schemes=["bcrypt_sha256"],
    default="bcrypt_sha256",
    deprecated=[]
)

app.mount("/static", StaticFiles(directory="frontend"), name="static")


class Blog(BaseModel):
    title: str
    content: str


class SignupRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


blogs = []


@app.get("/")
def root():
    return {"message": "CMS alive"}


@app.get("/login", response_class=HTMLResponse)
def get_login_page():
    return FileResponse("frontend/login.html")


@app.get("/signup", response_class=HTMLResponse)
def serve_signup():
    return FileResponse("frontend/signup.html")


@app.post("/signup")
def signup(data: SignupRequest):

    existing_user = users_collection.find_one({"email": data.email})

    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")

    hashed_password = pwd_context.hash(data.password)

    users_collection.insert_one({
        "username": data.username,
        "email": data.email,
        "password": hashed_password
    })

    return {"message": "User created successfully"}


@app.post("/login")
def login(data: LoginRequest):

    user = users_collection.find_one({"email": data.email})

    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not pwd_context.verify(data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {"message": "Login successful"}


@app.get("/login/github")
async def login_github(request: Request):

    redirect_uri = str(request.url_for("github_callback"))
    print("REDIRECT URI SENT TO GITHUB:", redirect_uri)

    return await oauth.github.authorize_redirect(
        request,
        redirect_uri
    )


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


@app.get("/dashboard", response_class=HTMLResponse)
def dashboard():
    return FileResponse("frontend/index.html")


@app.post("/blogs")
def create_blog(blog: Blog):
    blogs.append(blog)
    return {"message": "Blog created", "data": blog}


@app.get("/blogs", response_model=List[Blog])
def get_blogs():
    return blogs
