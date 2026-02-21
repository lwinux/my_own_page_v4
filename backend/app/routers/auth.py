from fastapi import APIRouter, Depends, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.dependencies import get_db
from app.schemas.auth import (
    LoginRequest,
    RefreshRequest,
    RefreshResponse,
    RegisterRequest,
    TokenResponse,
    UserOut,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])

# Module-level limiter — the shared instance is attached to app.state in main.py
_limiter = Limiter(key_func=get_remote_address)


@router.post("/register", response_model=UserOut, status_code=201)
@_limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def register(
    request: Request,
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await AuthService(db).register(body)
    return UserOut(
        id=str(user.id),
        email=user.email,
        username=user.username,
        is_active=user.is_active,
    )


@router.post("/login", response_model=TokenResponse)
@_limiter.limit(get_settings().RATE_LIMIT_AUTH)
async def login(
    request: Request,
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).login(body)


@router.post("/refresh", response_model=RefreshResponse)
@_limiter.limit("30/minute")
async def refresh(
    request: Request,
    body: RefreshRequest,
    db: AsyncSession = Depends(get_db),
):
    return await AuthService(db).refresh(body.refresh_token)


@router.post("/logout", status_code=204)
async def logout():
    """
    Stateless JWT logout — client is responsible for discarding tokens.
    Extend with a Redis blocklist for server-side invalidation.
    """
    return None
