"""基础模型混入类"""
from sqlalchemy import Column, DateTime, func
from app.database import Base


class TimestampMixin:
    """为所有模型添加创建和更新时间戳"""
    created_at = Column(DateTime, default=func.now(), comment="创建时间")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="更新时间")
