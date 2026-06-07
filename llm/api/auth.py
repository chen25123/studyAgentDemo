"""Auth API —— JWT 登录认证。"""

import hashlib
from datetime import UTC, datetime, timedelta

import jwt
from fastapi import APIRouter, Header
from pydantic import BaseModel, Field
from sqlalchemy import text

from llm.config import JWT_SECRET
from llm.repositories.db import get_engine

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class LoginResponse(BaseModel):
    token: str
    username: str
    display_name: str
    role_code: str


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    pw_hash = hashlib.sha256(req.password.encode()).hexdigest()

    with get_engine().connect() as conn:
        row = conn.execute(
            text(
                "SELECT id, username, display_name, role_code "
                "FROM users WHERE username = :un AND password_hash = :pw "
                "AND status = 'active' AND deleted_at IS NULL"
            ),
            {"un": req.username, "pw": pw_hash},
        ).mappings().first()

    if row is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="用户名或密码错误")

    payload = {
        "sub": str(row["id"]),
        "username": row["username"],
        "display_name": row["display_name"],
        "role_code": row["role_code"],
        "exp": datetime.now(UTC) + timedelta(hours=24),
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")

    return LoginResponse(
        token=token,
        username=row["username"],
        display_name=row["display_name"],
        role_code=row["role_code"],
    )


@router.get("/me")
def me(authorization: str = Header(default="")):
    token = authorization.replace("Bearer ", "")
    if not token:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="未提供认证令牌")

    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.ExpiredSignatureError as err:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="令牌已过期") from err
    except jwt.InvalidTokenError as err:
        from fastapi import HTTPException
        raise HTTPException(status_code=401, detail="无效令牌") from err

    return {
        "user_id": payload["sub"],
        "username": payload["username"],
        "display_name": payload["display_name"],
        "role_code": payload["role_code"],
    }


def verify_token(token: str) -> dict | None:
    """解析 JWT token，返回 payload 或 None。"""
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        return None
