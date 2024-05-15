import typing
from fastapi.security import SecurityScopes
import pytest
from typing import Generator, Any

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.responses import ORJSONResponse

from app.api.auth_deps import get_auth_data, AuthData
from app.api import router as api_v1_router
from core.config import settings

# Since we import app.main, the code in it will be executed,
# including the definition of the table models.
#
# This hack will automatically register the tables in Base.metadata.
import app.main

# Create a PostgreSQL DB specifically for testing and
# keep the original DB untouched.
#
# Add echo=True in `create_engine` to log all DB commands made


@pytest.fixture(scope="session")
def app() -> Generator[FastAPI, Any, None]:
    """Create a new application for the test session."""

    _app = FastAPI(default_response_class=ORJSONResponse)
    _app.include_router(api_v1_router, prefix=settings.API_V1_STR)
    yield _app


@pytest.fixture(scope="function")
def client(
    request: pytest.FixtureRequest, app: FastAPI
) -> Generator[TestClient, Any, None]:
    """Create a new TestClient that uses the `app` and `db` fixture.

    The `db` fixture will override the `get_db` dependency that is
    injected into routes.
    """
    auth_data: AuthData = typing.cast(AuthData, getattr(request, "param", None))

    def pass_trough_auth() -> AuthData:
        return auth_data

    if auth_data:
        app.dependency_overrides[get_auth_data] = pass_trough_auth

    with TestClient(app) as client:
        yield client

    app.dependency_overrides.clear()
