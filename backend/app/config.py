"""应用配置模块"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """应用配置"""
    APP_NAME: str = "AI智能排课平台"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 数据库配置 - 使用SQLite便于开发
    DATABASE_URL: str = "sqlite:///./data/scheduling.db"

    # 排课参数默认值
    MAX_GENERATIONS: int = 500
    POPULATION_SIZE: int = 100
    MUTATION_RATE: float = 0.1
    CROSSOVER_RATE: float = 0.8

    # 每周上课天数（默认周一至周五）
    WEEKDAYS: int = 5
    # 每天上课节数（默认8节）
    PERIODS_PER_DAY: int = 8

    # CORS配置
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000"]

    model_config = {"env_file": ".env", "case_sensitive": True}


settings = Settings()
