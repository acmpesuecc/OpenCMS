from fastapi import FastAPI, Request
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel
from typing import List
from fastapi.templating import Jinja2Templates
from bson import ObjectId
import os
from dotenv import load_dotenv
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

client = AsyncIOMotorClient(MONGO_URI)
db = client["OpenCMS"]
collection_types = db["collection_types"]
components = db["components"]

templates = Jinja2Templates(directory="templates")

app = FastAPI()

collection_schema= {
        "bsonType": "object",
        "properties":{
            "title": {
                "bsonType": "string",
            },
            "components": {
                "bsonType": "array",

                "items": {
                    "bsonType": "objectId"
                }
            }
        }
}

component_schema= {
        "bsonType": "object",
        "required":["name","type"],
        "properties":{
            "name":{
                "bsonType": "string",
            },
            "type":{
                "bsonType": "string",
            }
        }
}

class ComponentType(BaseModel):
    name: str
    type: str

class CollectionType(BaseModel):
    title: str
    components: List[str] = []  # array of component object id's


@app.get("/")
async def root(request: Request):
    return templates.TemplateResponse("collection_types.html", {"request": request})

@app.post("/fieldtypes")
async def func(collection_type: CollectionType):
    # collection_data= await request.json() 
    # collectionJson= {
    #     "title": collection_type.get("title", ""),
    #     "components": collection_type.get("components", [])
    # }
    try:
        data=collection_type.model_dump()
        # comps=data["components"]
        # for i in range(len(data["components"])):
        #     data["components"][i]=ObjectId(data["components"][i])

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

# async def func(request: Request):

#     result= await components.find().to_list(100)
#     return templates.TemplateResponse(
#         "collection_types.html",
#         {
#             "request": request,
#             "collections": result
#         }
#     )

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
async def updatefield(fieldId:str):
    await collection_types.update_one(
        {"_id": ObjectId(fieldId)},
        {"$set": {"components": [ObjectId(c) for c in collection_types.components]}}
    )
    return {"message": "Updated"}
