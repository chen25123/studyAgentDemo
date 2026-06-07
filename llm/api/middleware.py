"""API 中间件。"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from llm.api.auth import verify_token
from llm.config import ADMIN_TOKEN
from llm.schemas.error import ErrorCode, ErrorResponse


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """Admin 路由鉴权 —— 支持 JWT (admin 角色) 或 X-Admin-Token。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        if not request.url.path.startswith("/api/admin"):
            return await call_next(request)

        # 方式 1：X-Admin-Token（向后兼容）
        if ADMIN_TOKEN:
            xt = request.headers.get("X-Admin-Token", "")
            if xt == ADMIN_TOKEN:
                return await call_next(request)

        # 方式 2：JWT Bearer Token（需 admin 角色）
        auth = request.headers.get("Authorization", "")
        token = auth.replace("Bearer ", "")
        if token:
            payload = verify_token(token)
            if payload and payload.get("role_code") == "admin":
                return await call_next(request)

        return JSONResponse(
            status_code=403,
            content=ErrorResponse(
                error_code=ErrorCode.PERMISSION_DENIED,
                message="缺少或无效的认证凭据（需 admin 角色或有效的 Admin Token）",
                retryable=False,
            ).model_dump(),
        )
