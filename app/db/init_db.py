import os

from pymongo import MongoClient

from app.core.config import settings

client = MongoClient(str(settings.MONGO_URI))
db = client[settings.MONGO_DB]

offers_collection = db["offers"]
payments_collection = db["payments"]

def get_db():
    return db
