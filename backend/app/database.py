"""数据库连接与会话管理"""
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

# 创建引擎
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
    echo=settings.DEBUG,
)

# 启用SQLite外键约束
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    if "sqlite" in settings.DATABASE_URL:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基类
Base = declarative_base()


def get_db():
    """获取数据库会话（依赖注入）"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """初始化数据库表结构（含自动迁移）"""
    Base.metadata.create_all(bind=engine)
    _migrate_course_columns(engine)


def _migrate_course_columns(engine):
    """SQLite 兼容迁移：重命名 weekly_hours → semester_sessions + 新增列"""
    import sqlite3
    from sqlalchemy import text, inspect

    # 仅 SQLite 需要手动迁移
    if "sqlite" not in str(engine.url):
        return

    with engine.connect() as conn:
        # 获取现有列名
        existing = {row[1] for row in conn.execute(text("PRAGMA table_info(courses)")).fetchall()}

        # 1. 如果旧列 weekly_hours 存在且新列 semester_sessions 不存在，执行重命名
        if "weekly_hours" in existing and "semester_sessions" not in existing:
            try:
                conn.execute(text("ALTER TABLE courses RENAME COLUMN weekly_hours TO semester_sessions"))
                conn.commit()
                existing.discard("weekly_hours")
                existing.add("semester_sessions")
            except Exception:
                pass  # 忽略迁移错误（列可能已被其他方式处理）

        # 2. 新增 weekly_sessions 列
        if "weekly_sessions" not in existing:
            try:
                conn.execute(text("ALTER TABLE courses ADD COLUMN weekly_sessions INTEGER NOT NULL DEFAULT 1"))
                conn.commit()
            except Exception:
                pass

        # 3. 新增 hours_per_session 列
        if "hours_per_session" not in existing:
            try:
                conn.execute(text("ALTER TABLE courses ADD COLUMN hours_per_session INTEGER NOT NULL DEFAULT 2"))
                conn.commit()
            except Exception:
                pass
