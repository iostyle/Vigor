from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.api.admin.categories import router as admin_categories_router
from app.api.admin.keywords import router as admin_keywords_router
from app.api.admin.scheduled_tasks import router as admin_scheduled_tasks_router
from app.api.admin.tasks import router as admin_tasks_router
from app.api.admin.videos import router as admin_videos_router
from app.api.internal.categories import router as internal_categories_router
from app.api.internal.stats import router as internal_stats_router
from app.api.internal.videos import router as internal_videos_router
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(
    title="Vigor Server",
    description="Vigor 数据采集与分析平台服务端",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(admin_categories_router, prefix="/api/admin")
app.include_router(admin_keywords_router, prefix="/api/admin")
app.include_router(admin_tasks_router)
app.include_router(admin_scheduled_tasks_router)
app.include_router(admin_videos_router)
app.include_router(internal_categories_router, prefix="/api/internal")
app.include_router(internal_videos_router, prefix="/api/internal")
app.include_router(internal_stats_router, prefix="/api/internal")


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics", tags=["system"])
def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
