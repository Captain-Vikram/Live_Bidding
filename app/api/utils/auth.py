from sqlalchemy.ext.asyncio import AsyncSession
import random
import string
from datetime import datetime, timedelta
from typing import Optional
from fastapi import WebSocket, status, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from jose import jwt

from app.core.config import settings
from app.core.database import get_db
from app.db.managers.accounts import jwt_manager
from app.db.models.accounts import User

ALGORITHM = "HS256"
security = HTTPBearer()


class Authentication:
    # generate random string
    def get_random(length: int):
        return "".join(random.choices(string.ascii_letters + string.digits, k=length))

    # generate access token based and encode user's id
    async def create_access_token(payload: dict):
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
        to_encode = {"exp": expire, **payload}
        encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)
        return encoded_jwt

    # generate random refresh token
    async def create_refresh_token(
        expire=datetime.utcnow()
        + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
    ):
        return jwt.encode(
            {"exp": expire, "data": Authentication.get_random(10)},
            settings.SECRET_KEY,
            algorithm=ALGORITHM,
        )

    # deocde access token from header
    async def decode_jwt(token: str):
        try:
            decoded = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        except:
            decoded = False
        return decoded

    async def decodeAuthorization(db: AsyncSession, token: str):
        decoded = await Authentication.decode_jwt(token)
        if not decoded:
            return None
        jwt_obj = await jwt_manager.get_by_user_id(db, decoded["user_id"])
        if not jwt_obj:
            return None
        return jwt_obj.user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Get current authenticated user from HTTP request"""
    try:
        user = await Authentication.decodeAuthorization(db, credentials.credentials)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_ws(websocket: WebSocket, db: AsyncSession) -> User:
    """Get current authenticated user from WebSocket connection"""
    try:
        # Get token from query parameters or headers
        token = None
        
        # Try to get token from query parameters first
        if "token" in websocket.query_params:
            token = websocket.query_params["token"]
        elif "authorization" in websocket.query_params:
            auth_header = websocket.query_params["authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
        
        # Try to get token from headers if not in query params
        if not token and "authorization" in websocket.headers:
            auth_header = websocket.headers["authorization"]
            if auth_header.startswith("Bearer "):
                token = auth_header[7:]
        
        if not token:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Missing authentication token")
            raise Exception("Missing authentication token")
        
        # Use the passed database session
        user = await Authentication.decodeAuthorization(db, token)
        if not user:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid authentication token")
            raise Exception("Invalid authentication token")
        return user
        
    except Exception as e:
        if websocket.client_state.value == 1:  # Connected state
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Authentication failed")
        raise Exception(f"WebSocket authentication failed: {e}")


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    if not credentials:
        return None
    
    try:
        user = await Authentication.decodeAuthorization(db, credentials.credentials)
        return user
    except Exception:
        return None
