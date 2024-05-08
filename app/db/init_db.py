import os
from typing import Generator

import motor.motor_asyncio

from app.core.config import settings

client = motor.motor_asyncio.AsyncIOMotorClient(str(settings.MONGO_URI))

db = client.get_database(settings.MONGO_DB)

offers_collection = db.get_collection("offers")
payments_collection = db.get_collection("payments")

def get_db() -> Generator:
    # FIXME: is this necessary?
    try:
        yield db
    finally:
        client.close()
