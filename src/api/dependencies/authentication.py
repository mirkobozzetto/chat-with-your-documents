# src/api/dependencies/authentication.py
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional

from src.auth.api_auth_manager import ApiAuthManager
from src.api.models.auth_models import UserInfo
from src.security.key_manager import KeyManager

security = HTTPBearer()
key_manager = KeyManager()

JWT_SECRET_KEY = key_manager.get_jwt_secret_key()
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

def create_jwt_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a new JWT token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_jwt_token(token: str) -> Optional[str]:
    """Verify and extract username from JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        return username
    except JWTError:
        return None

def get_auth_manager() -> ApiAuthManager:
    """Get auth manager instance"""
    return ApiAuthManager()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_manager: ApiAuthManager = Depends(get_auth_manager)
) -> UserInfo:
    """Get current authenticated user (required)"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    username = verify_jwt_token(credentials.credentials)
    if username is None:
        raise credentials_exception

    if not auth_manager.is_auth_enabled():
        return UserInfo(username=username, is_authenticated=True)

    if not auth_manager.user_exists(username):
        raise credentials_exception

    return UserInfo(username=username, is_authenticated=True)

def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_manager: ApiAuthManager = Depends(get_auth_manager)
) -> Optional[UserInfo]:
    """Get current user if authenticated (optional)"""
    if not auth_manager.is_auth_enabled():
        return UserInfo(username="anonymous", is_authenticated=True)

    if not credentials:
        return None

    username = verify_jwt_token(credentials.credentials)
    if username is None:
        return None

    if not auth_manager.user_exists(username):
        return None

    return UserInfo(username=username, is_authenticated=True)
