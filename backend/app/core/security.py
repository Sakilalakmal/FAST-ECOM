from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Literal
from uuid import uuid4

import jwt
from jwt import InvalidTokenError
from pydantic import BaseModel
from pwdlib import PasswordHash

from app.core.config import get_settings

TokenType = Literal["access", "refresh"]

password_hasher = PasswordHash.recommended()


class EncodedToken(BaseModel):
    token: str
    expires_at: datetime


class TokenPayload(BaseModel):
    sub: str
    type: TokenType
    exp: int
    iat: int
    iss: str
    jti: str | None = None


def get_password_hash(password: str) -> str:
    return password_hasher.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hasher.verify(password, hashed_password)


def generate_token_jti() -> str:
    return uuid4().hex


def create_access_token(*, subject: str) -> EncodedToken:
    settings = get_settings()
    expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return _encode_token(
        subject=subject,
        token_type="access",
        expires_delta=expires_delta,
    )


def create_refresh_token(*, subject: str, jti: str) -> EncodedToken:
    settings = get_settings()
    expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return _encode_token(
        subject=subject,
        token_type="refresh",
        expires_delta=expires_delta,
        jti=jti,
    )


def decode_token(token: str, *, expected_type: TokenType | None = None) -> TokenPayload:
    settings = get_settings()
    decoded = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
        issuer=settings.JWT_ISSUER,
    )
    payload = TokenPayload.model_validate(decoded)

    if expected_type and payload.type != expected_type:
        raise InvalidTokenError(f"Expected a {expected_type} token.")

    return payload


def _encode_token(
    *,
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    jti: str | None = None,
) -> EncodedToken:
    settings = get_settings()
    issued_at = datetime.now(UTC)
    expires_at = issued_at + expires_delta
    payload = {
        "sub": subject,
        "type": token_type,
        "iat": issued_at,
        "exp": expires_at,
        "iss": settings.JWT_ISSUER,
    }

    if jti is not None:
        payload["jti"] = jti

    token = jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )
    return EncodedToken(token=token, expires_at=expires_at)
