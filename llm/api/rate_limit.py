"""简单 IP-based token bucket 限流中间件。"""

import time
from collections import defaultdict

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from llm.schemas.error import ErrorCode, ErrorResponse


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token bucket 限流 —— 保护 /api/chat 接口。

    默认：每 IP 每分钟 10 次请求。
    """

    _buckets: defaultdict[str, list[float]] = defaultdict(list)

    def __init__(self, app, limit: int = 10, window: float = 60.0):
        super().__init__(app)
        self.limit = limit
        self.window = window

    async def dispatch(self, request: Request, call_next) -> Response:
        if request.url.path not in ("/api/chat", "/api/chat/stream"):
            return await call_next(request)

        now = time.time()
        ip = request.client.host if request.client else "unknown"

        # 清理过期记录
        bucket = self._buckets[ip]
        cutoff = now - self.window
        while bucket and bucket[0] < cutoff:
            bucket.pop(0)

        if len(bucket) >= self.limit:
            return JSONResponse(
                status_code=429,
                content=ErrorResponse(
                    error_code=ErrorCode.PERMISSION_DENIED,
                    message=f"请求过于频繁，每分钟限 {self.limit} 次。请稍后重试。",
                    retryable=True,
                ).model_dump(),
            )

        bucket.append(now)
        return await call_next(request)
