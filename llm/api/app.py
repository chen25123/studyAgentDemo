from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from llm.api.chat import router as chat_router
from llm.api.llm_trace import router as llm_trace_router
from llm.config import FRONTEND_ORIGIN


def create_app() -> FastAPI:
    app = FastAPI(title="DevFlow Agent API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[FRONTEND_ORIGIN],
        allow_credentials=True,
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(chat_router)
    app.include_router(llm_trace_router)

    return app


app = create_app()
