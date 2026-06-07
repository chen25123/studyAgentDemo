"""API 中间件。"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from llm.config import ADMIN_TOKEN
from llm.schemas.error import ErrorCode, ErrorResponse


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """X-Admin-Token 校验 —— 保护 /api/admin/* 路由。"""

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path.startswith("/api/admin"):
            token = request.headers.get("X-Admin-Token", "")
            if not ADMIN_TOKEN or token != ADMIN_TOKEN:
                return JSONResponse(
                    status_code=403,
                    content=ErrorResponse(
                        error_code=ErrorCode.PERMISSION_DENIED,
                        message="缺少或无效的 Admin Token",
                        retryable=False,
                    ).model_dump(),
                )
        return await call_next(request)
