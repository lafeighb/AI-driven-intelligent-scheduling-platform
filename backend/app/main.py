"""AI驱动一体化智能排课平台 - FastAPI主入口"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.database import init_db, engine, Base
from app.api import classes, teachers, courses, classrooms, schedules, constraints, import_export, auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：初始化数据库表
    init_db()
    yield
    # 关闭时：清理资源
    engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI驱动的一体化智能排课平台 - 支持多目标自动排课、冲突检测、约束学习与智能分析",
    lifespan=lifespan,
)

# CORS中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理 — 将 IntegrityError 转为友好的 JSON 错误响应
@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    detail = "数据操作冲突：可能存在关联数据，请先删除关联的排课记录后再操作"
    return JSONResponse(status_code=409, content={"detail": detail})


# 注册路由
app.include_router(classes.router)
app.include_router(teachers.router)
app.include_router(courses.router)
app.include_router(classrooms.router)
app.include_router(schedules.router)
app.include_router(constraints.router)
app.include_router(import_export.router)
app.include_router(auth.router)


@app.get("/", tags=["系统"])
def root():
    """系统根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs",
    }


@app.get("/api/health", tags=["系统"])
def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
    }
