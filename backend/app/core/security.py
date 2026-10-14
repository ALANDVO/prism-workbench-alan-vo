import secrets
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlencode

import httpx
from jose import jwt, JWTError
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(data: Dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_state() -> str:
    return secrets.token_urlsafe(32)


def generate_nonce() -> str:
    return secrets.token_urlsafe(32)


def generate_pkce_verifier() -> str:
    return secrets.token_urlsafe(64)[:128]


def generate_pkce_challenge(verifier: str) -> str:
    import base64
    import hashlib
    digest = hashlib.sha256(verifier.encode()).digest()
    return base64.urlsafe_b64encode(digest).decode().rstrip("=")


class OIDCClient:
    def __init__(self):
        self._discovery_cache: Optional[Dict[str, Any]] = None
        self._cache_time: float = 0
        self._cache_ttl = 3600

    async def get_discovery_document(self) -> Dict[str, Any]:
        now = time.time()
        if self._discovery_cache and (now - self._cache_time) < self._cache_ttl:
            return self._discovery_cache

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(settings.oidc_discovery_url)
            resp.raise_for_status()
            self._discovery_cache = resp.json()
            self._cache_time = now
            return self._discovery_cache

    async def get_authorization_url(self, state: str, nonce: str, pkce_challenge: str) -> str:
        discovery = await self.get_discovery_document()
        auth_endpoint = discovery.get("authorization_endpoint") or settings.OIDC_AUTHORIZATION_ENDPOINT
        if not auth_endpoint:
            raise ValueError("Authorization endpoint not configured")

        params = {
            "response_type": "code",
            "client_id": settings.OIDC_CLIENT_ID,
            "redirect_uri": settings.OIDC_REDIRECT_URI,
            "scope": " ".join(settings.OIDC_SCOPES),
            "state": state,
            "nonce": nonce,
            "code_challenge": pkce_challenge,
            "code_challenge_method": "S256",
        }
        return f"{auth_endpoint}?{urlencode(params)}"

    async def exchange_code_for_tokens(self, code: str, pkce_verifier: str) -> Dict[str, Any]:
        discovery = await self.get_discovery_document()
        token_endpoint = discovery.get("token_endpoint") or settings.OIDC_TOKEN_ENDPOINT
        if not token_endpoint:
            raise ValueError("Token endpoint not configured")

        async with httpx.AsyncClient(timeout=10.0) as client:
            data = {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": settings.OIDC_REDIRECT_URI,
                "client_id": settings.OIDC_CLIENT_ID,
                "code_verifier": pkce_verifier,
            }
            if settings.OIDC_CLIENT_SECRET:
                data["client_secret"] = settings.OIDC_CLIENT_SECRET

            resp = await client.post(token_endpoint, data=data)
            resp.raise_for_status()
            return resp.json()

    async def get_userinfo(self, access_token: str) -> Dict[str, Any]:
        discovery = await self.get_discovery_document()
        userinfo_endpoint = discovery.get("userinfo_endpoint") or settings.OIDC_USERINFO_ENDPOINT
        if not userinfo_endpoint:
            raise ValueError("Userinfo endpoint not configured")

        async with httpx.AsyncClient(timeout=10.0) as client:
            headers = {"Authorization": f"Bearer {access_token}"}
            resp = await client.get(userinfo_endpoint, headers=headers)
            resp.raise_for_status()
            return resp.json()

    async def get_logout_url(self, id_token_hint: Optional[str] = None) -> str:
        discovery = await self.get_discovery_document()
        logout_endpoint = discovery.get("end_session_endpoint") or settings.OIDC_LOGOUT_ENDPOINT
        if not logout_endpoint:
            return f"{settings.OIDC_ISSUER_URL.rstrip('/')}/protocol/openid-connect/logout"

        params = {"post_logout_redirect_uri": settings.OIDC_REDIRECT_URI.replace("/auth/callback", "/")}
        if id_token_hint:
            params["id_token_hint"] = id_token_hint
        return f"{logout_endpoint}?{urlencode(params)}"

    async def validate_id_token(self, id_token: str, nonce: str) -> Dict[str, Any]:
        discovery = await self.get_discovery_document()
        jwks_uri = discovery.get("jwks_uri") or settings.OIDC_JWKS_URI

        if not jwks_uri:
            raise ValueError("JWKS URI not available")

        async with httpx.AsyncClient(timeout=10.0) as client:
            jwks_resp = await client.get(jwks_uri)
            jwks_resp.raise_for_status()
            jwks = jwks_resp.json()

        unverified_header = jwt.get_unverified_header(id_token)
        kid = unverified_header.get("kid")
        if not kid:
            raise JWTError("No kid in token header")

        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
        if not key:
            raise JWTError("Key not found in JWKS")

        from jose import jwk
        public_key = jwk.construct(key)

        payload = jwt.decode(
            id_token,
            public_key.to_pem().decode(),
            algorithms=["RS256"],
            audience=settings.OIDC_CLIENT_ID,
            issuer=settings.OIDC_ISSUER_URL,
        )

        if payload.get("nonce") != nonce:
            raise JWTError("Invalid nonce")

        return payload


oidc_client = OIDCClient()


class SessionManager:
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}

    def create_session(self, user_data: Dict[str, Any]) -> str:
        session_id = secrets.token_urlsafe(32)
        self._sessions[session_id] = {
            "user": user_data,
            "created_at": time.time(),
            "last_accessed": time.time(),
        }
        return session_id

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        session = self._sessions.get(session_id)
        if session:
            session["last_accessed"] = time.time()
            return session
        return None

    def delete_session(self, session_id: str) -> bool:
        return self._sessions.pop(session_id, None) is not None

    def cleanup_expired(self, max_age: int = 86400) -> int:
        now = time.time()
        expired = [sid for sid, s in self._sessions.items() if now - s["last_accessed"] > max_age]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)


session_manager = SessionManager()