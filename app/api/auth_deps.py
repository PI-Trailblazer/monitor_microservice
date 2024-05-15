from urllib import request
from fastapi import Depends, HTTPException, status
from fastapi.responses import JSONResponse, Response

from pydantic import BaseModel, ValidationError
from jose import JWTError, jwt
from datetime import datetime, timezone
from typing import Annotated, Any, Dict, List, Literal, Optional, Set, Union
from loguru import logger
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, SecurityScopes
from app.core.config import settings

ACCESS_TOKEN_TYPE: str = "access"
REFRESH_TOKEN_TYPE: str = "refresh"

with open(settings.JWT_SECRET_KEY_PATH) as f:
    private_key = f.read()

with open(settings.JWT_PUBLIC_KEY_PATH) as f:
    public_key = f.read()

auth_response: Dict[Union[int, str], Dict[str, Any]] = {
    401: {"description": "Not Authenticated"},
    403: {"description": "Not Authorized"},
}


class ProprietaryToken(HTTPBearer):
    def __init__(self, *, auto_error: bool = True):
        super().__init__(auto_error=auto_error)


secure = ProprietaryToken(auto_error=False)


class Token(BaseModel):
    access_token: str
    token_type: str


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        public_key,
        algorithms=[settings.JWT_ALGORITHM],
        options={
            "require_exp": True,
            "require_iat": True,
            "require_sub": True,
        },
    )


class AuthData(BaseModel):
    sub: str
    name: str
    scopes: List[str]
    tags: List[str]


async def get_auth_data(
    cred: str = Depends(secure),
) -> Optional[AuthData]:
    token = cred.credentials
    if token is None:
        return None

    try:
        payload = decode_token(token)
        token_type = payload["type"]
    except JWTError:
        return None

    if token_type != ACCESS_TOKEN_TYPE:
        return None

    try:
        auth_data = AuthData(**payload)
    except ValidationError as e:
        logger.debug(e)
        return None

    return auth_data


GetAuthData = Annotated[Optional[AuthData], Depends(get_auth_data)]


async def verify_token(
    security_scopes: SecurityScopes, auth_data: GetAuthData
) -> AuthData:
    """Dependency for user authentication"""
    if security_scopes.scopes:
        authenticate_value = f'Bearer scope="{security_scopes.scope_str}"'
    else:
        authenticate_value = "Bearer"
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": authenticate_value},
    )

    if auth_data is None:
        raise credentials_exception
    # Verify that the token has all the necessary scopes
    for scope in security_scopes.scopes:
        if scope not in auth_data.scopes:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not enough permissions",
                headers={"WWW-Authenticate": authenticate_value},
            )

    return auth_data
