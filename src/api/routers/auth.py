# src/api/routers/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from datetime import timedelta

from src.api.models.auth_models import LoginRequest, TokenResponse, AuthStatusResponse, UserInfo
from src.api.dependencies.authentication import get_auth_manager, create_jwt_token, get_optional_current_user
from src.auth.api_auth_manager import ApiAuthManager

router = APIRouter(prefix="/api/auth", tags=["auth"])

ACCESS_TOKEN_EXPIRE_MINUTES = 30


@router.post("/login", response_model=TokenResponse)
async def login(
    request: LoginRequest,
    auth_manager: ApiAuthManager = Depends(get_auth_manager)
):
    if not auth_manager.is_auth_enabled():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authentication is not enabled"
        )

    is_valid = auth_manager.authenticate_user(request.username, request.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_jwt_token(
        data={"sub": request.username}, expires_delta=access_token_expires
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status(
    current_user: UserInfo = Depends(get_optional_current_user),
    auth_manager: ApiAuthManager = Depends(get_auth_manager)
):
    auth_required = auth_manager.is_auth_enabled()

    return AuthStatusResponse(
        is_authenticated=current_user is not None,
        user_info=current_user,
        auth_required=auth_required
    )


@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out"}
