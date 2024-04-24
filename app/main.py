from contextlib import asynccontextmanager
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import ORJSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.api import router as api_router
from app.core.config import settings
from app.db.init_db import get_db, offers_collection


@asynccontextmanager
async def lifespan(_: FastAPI):
    get_db()
    yield

app = FastAPI(
    title="Monitor Microservice",
    lifespan=lifespan,
    description="This is a very fancy project, with auto docs for the API and everything",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# class Offer(BaseModel):
#     name: str
#     description: str
#     # Adicione mais campos aqui conforme necessário

# @app.post("/offers/")
# async def create_offer(offer: Offer):
#     offer_dict = offer.dict()
#     result = await offers_collection.insert_one(offer_dict)           # Used just for testing
#     offer_dict["_id"] = str(result.inserted_id)
#     return offer_dict

# @app.get("/offers/", response_model=List[Offer])
# async def read_offers():
#     offers = []
#     for offer in await offers_collection.find().to_list(length=100):
#         offer["_id"] = str(offer["_id"])
#         offers.append(offer)
#     return offers


app.include_router(api_router, prefix="/api")
