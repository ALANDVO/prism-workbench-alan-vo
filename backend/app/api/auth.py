from datetime import datetime, timezone
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.config import settings
from app.core.database import get_db_session
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_nonce,
    generate_pkce_challenge,
    generate_pkce_verifier,
    generate_state,
    oidc_client,
    session_manager,
    verify_password,
)
from app.models.user import User, UserRole

router = APIRouter(prefix="/auth", tags=["auth"])


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserInfo(BaseModel):
    id: int
    subject: str
    email: Optional[str] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    role: UserRole
    is_active: bool


class LoginRequest(BaseModel):
    email: str
    password: str


def get_session_cookie_name() -> str:
    return settings.SESSION_COOKIE_NAME


def set_session_cookie(response: Response, session_id: str) -> None:
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=session_id,
        httponly=settings.SESSION_COOKIE_HTTPONLY,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite=settings.SESSION_COOKIE_SAMESITE,
        domain=settings.SESSION_COOKIE_DOMAIN,
        path=settings.SESSION_COOKIE_PATH,
        max_age=60 * 60 * 24 * 7,
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        domain=settings.SESSION_COOKIE_DOMAIN,
        path=settings.SESSION_COOKIE_PATH,
    )


def get_current_session(request: Request) -> Optional[str]:
    return request.cookies.get(settings.SESSION_COOKIE_NAME)


async def get_current_user(
    request: Request,
    session: AsyncSession = Depends(get_db_session),
) -> Optional[User]:
    session_id = get_current_session(request)
    if not session_id:
        return None

    session_data = session_manager.get_session(session_id)
    if not session_data:
        return None

    user_id = session_data.get("user", {}).get("id")
    if not user_id:
        return None

    result = await session.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        return None

    return user


async def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user


async def require_operator(user: User = Depends(require_user)) -> User:
    if user.role not in (UserRole.OPERATOR, UserRole.ADMIN):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Operator or admin role required")
    return user


async def require_admin(user: User = Depends(require_user)) -> User:
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin role required")
    return user


@router.get("/login")
async def login(request: Request) -> RedirectResponse:
    if not settings.OIDC_ENABLED:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="OIDC not enabled")

    state = generate_state()
    nonce = generate_nonce()
    pkce_verifier = generate_pkce_verifier()
    pkce_challenge = generate_pkce_challenge(pkce_verifier)

    request.session = {"oidc_state": state, "oidc_nonce": nonce, "oidc_pkce_verifier": pkce_verifier}

    auth_url = await oidc_client.get_authorization_url(state, nonce, pkce_challenge)
    return RedirectResponse(url=auth_url)


@router.get("/callback")
async def callback(
    request: Request,
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    if not settings.OIDC_ENABLED:
        raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="OIDC not enabled")

    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"OIDC error: {error} - {error_description}",
        )

    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing code or state")

    stored_state = request.session.get("oidc_state") if hasattr(request, "session") else None
    stored_nonce = request.session.get("oidc_nonce") if hasattr(request, "session") else None
    pkce_verifier = request.session.get("oidc_pkce_verifier") if hasattr(request, "session") else None

    if not stored_state or stored_state != state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid state")

    if not stored_nonce or not pkce_verifier:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing nonce or PKCE verifier")

    try:
        token_response = await oidc_client.exchange_code_for_tokens(code, pkce_verifier)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Token exchange failed: {e}")

    access_token = token_response.get("access_token")
    id_token = token_response.get("id_token")
    refresh_token = token_response.get("refresh_token")

    if not access_token or not id_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing tokens in response")

    try:
        id_token_claims = await oidc_client.validate_id_token(id_token, stored_nonce)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"ID token validation failed: {e}")

    subject = id_token_claims.get("sub")
    email = id_token_claims.get("email")
    username = id_token_claims.get("preferred_username") or email
    full_name = id_token_claims.get("name")
    avatar_url = id_token_claims.get("picture")

    if not subject:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing subject in ID token")

    result = await session.execute(select(User).where(User.subject == subject))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            subject=subject,
            email=email,
            username=username,
            full_name=full_name,
            avatar_url=avatar_url,
            role=UserRole.VIEWER,
            is_active=True,
        )
        session.add(user)
        await session.flush()
    else:
        user.email = email or user.email
        user.username = username or user.username
        user.full_name = full_name or user.full_name
        user.avatar_url = avatar_url or user.avatar_url
        user.last_login = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(user)

    session_id = session_manager.create_session(
        {
            "id": user.id,
            "subject": user.subject,
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
            "access_token": access_token,
            "refresh_token": refresh_token,
            "id_token": id_token,
        }
    )

    response = RedirectResponse(url=settings.OIDC_REDIRECT_URI.replace("/auth/callback", "/dashboard"))
    set_session_cookie(response, session_id)

    if hasattr(request, "session"):
        request.session.clear()

    return response




@router.get("/me", response_model=UserInfo)
async def me(user: User = Depends(require_user)) -> UserInfo:
    return UserInfo(
        id=user.id,
        subject=user.subject,
        email=user.email,
        username=user.username,
        full_name=user.full_name,
        avatar_url=user.avatar_url,
        role=user.role,
        is_active=user.is_active,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, session: AsyncSession = Depends(get_db_session)) -> TokenResponse:
    session_id = get_current_session(request)
    if not session_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No session")

    session_data = session_manager.get_session(session_id)
    if not session_data:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid session")

    refresh_token = session_data.get("user", {}).get("refresh_token")
    if not refresh_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="No refresh token")

    try:
        discovery = await oidc_client.get_discovery_document()
        token_endpoint = discovery.get("token_endpoint") or settings.OIDC_TOKEN_ENDPOINT
        if not token_endpoint:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token endpoint not configured")

        async with httpx.AsyncClient(timeout=10.0) as client:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": settings.OIDC_CLIENT_ID,
            }
            if settings.OIDC_CLIENT_SECRET:
                data["client_secret"] = settings.OIDC_CLIENT_SECRET

            resp = await client.post(token_endpoint, data=data)
            resp.raise_for_status()
            new_tokens = resp.json()

        new_access_token = new_tokens.get("access_token")
        new_refresh_token = new_tokens.get("refresh_token", refresh_token)
        new_id_token = new_tokens.get("id_token")

        if not new_access_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No access token in refresh response")

        session_data["user"]["access_token"] = new_access_token
        session_data["user"]["refresh_token"] = new_refresh_token
        if new_id_token:
            session_data["user"]["id_token"] = new_id_token

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Token refresh failed: {e}")


@router.post("/logout")
async def logout(request: Request, response: Response) -> dict:
    session_id = get_current_session(request)
    if session_id:
        session_manager.delete_session(session_id)
    clear_session_cookie(response)
    return {"detail": "Logged out"}




@router.get("/demo-login")
async def demo_login(
    response: Response,
    session: AsyncSession = Depends(get_db_session),
) -> RedirectResponse:
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo mode is disabled. Set DEMO_MODE=true to enable.",
        )

    result = await session.execute(select(User).where(User.subject == "demo-user"))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            subject="demo-user",
            email="demo@prism.local",
            username="demo",
            full_name="Demo User",
            role=UserRole.OPERATOR,
            is_active=True,
        )
        session.add(user)
        await session.flush()
    else:
        user.last_login = datetime.now(timezone.utc)
        user.updated_at = datetime.now(timezone.utc)

    await session.commit()
    await session.refresh(user)

    session_id = session_manager.create_session(
        {
            "id": user.id,
            "subject": user.subject,
            "email": user.email,
            "username": user.username,
            "role": user.role.value,
        }
    )

    response = RedirectResponse(url="/dashboard")
    set_session_cookie(response, session_id)
    return response


import httpx