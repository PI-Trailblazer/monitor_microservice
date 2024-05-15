import os
import pathlib
from datetime import timedelta
from typing import List, Optional, Union

from pydantic import MongoDsn, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project Directories
ROOT = pathlib.Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=True
    )

    PRODUCTION: bool = os.getenv("ENV") == "production"

    API_V1_STR: str = "/api"
    STATIC_STR: str = "/static"

    HOST: str = "www.google.pt" if PRODUCTION else "http://localhost"
    STATIC_URL: str = HOST + STATIC_STR
    # BACKEND_CORS_ORIGINS is a JSON-formatted list of origins
    BACKEND_CORS_ORIGINS: List[str] = [HOST] + (
        [] if PRODUCTION else ["http://localhost:3000"]
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    # MongoDB

    MONGO_SERVER: str = os.getenv("MONGO_SERVER", "localhost")
    MONGO_USER: str = os.getenv("MONGO_USER", "mongo")
    MONGO_PASSWORD: str = os.getenv("MONGO_PASSWORD", "mongo")
    MONGO_DB: str = os.getenv("MONGO_DB", "monitor_db")
    MONGO_URI: Optional[MongoDsn] = (
        f"mongodb://{MONGO_USER}"
        f":{MONGO_PASSWORD}@{MONGO_SERVER}"
        f":27017/{MONGO_DB}?authSource=admin"
    )
    TEST_MONGO_URI: Optional[MongoDsn] = (
        f"mongodb://{MONGO_USER}"
        f":{MONGO_PASSWORD}@{MONGO_SERVER}"
        f":27017/{MONGO_DB}_test??authSource=admin"
    )

    # RabbitMQ
    RABBITMQ_HOST: str = os.getenv("RABBITMQ_HOST", "rabbitmq")
    RABBITMQ_PORT: int = os.getenv("RABBITMQ_PORT", 5672)
    RABBITMQ_VIRTUAL_HOST: str = os.getenv("RABBITMQ_VIRTUAL_HOST", "/")
    RABBITMQ_USERNAME: str = os.getenv("RABBITMQ_USERNAME", "user")
    RABBITMQ_PASSWORD: str = os.getenv("RABBITMQ_PASSWORD", "user")

    # JWT
    JWT_SECRET_KEY_PATH: str = "./dev-keys/jwt-key"
    JWT_PUBLIC_KEY_PATH: str = "./dev-keys/jwt-key.pub"
    ACCESS_TOKEN_EXPIRE_MINUTES: timedelta = timedelta(hours=1)
    REFRESH_TOKEN_EXPIRE_MINUTES: timedelta = timedelta(days=7)
    JWT_ALGORITHM: str = "RS256"


settings = Settings()
