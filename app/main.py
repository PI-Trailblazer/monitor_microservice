from threading import Thread

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.api import router as api_router
from app.core.config import settings
from app.db.init_db import get_db
from app.rabbitmq.handler import consume_messages

app = FastAPI(
    title="Monitor Microservice",
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

app.include_router(api_router, prefix="/api")

@app.on_event("startup")
def lifespan():
    get_db()

@app.on_event("startup")
def startup_event():
    """
    Function to run at the startup of the FastAPI application.
    """
    # Start consuming messages in a separate thread
    thread = Thread(target=consume_messages)
    thread.start()