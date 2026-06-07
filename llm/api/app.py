from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from llm.api.auth import router as auth_router
from llm.api.catalog import router as catalog_router
from llm.api.chat import router as chat_router
from llm.api.dashboard import router as dashboard_router
from llm.api.llm_trace import router as llm_trace_router
from llm.api.middleware import AdminAuthMiddleware
from llm.api.rate_limit import RateLimitMiddleware
from llm.config import FRONTEND_ORIGIN
from llm.schemas.error import ErrorCode, ErrorResponse


def create_app() -> FastAPI:
    app = FastAPI(title="DevFlow Agent API")

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_ORIGIN],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    # 限流
    app.add_middleware(RateLimitMiddleware, limit=10, window=60.0)

    # Admin 鉴权
    app.add_middleware(AdminAuthMiddleware)

    # 全局异常处理
    @app.exception_handler(Exception)
    async def global_exception_handler(_request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error_code=ErrorCode.INTERNAL_ERROR,
                message=str(exc),
                retryable=True,
            ).model_dump(),
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth_router)
    app.include_router(catalog_router)
    app.include_router(chat_router)
    app.include_router(dashboard_router)
    app.include_router(llm_trace_router)

    return app


app = create_app()
