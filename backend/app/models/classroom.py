"""教室数据模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from app.database import Base
from app.models.base import TimestampMixin


class Classroom(Base, TimestampMixin):
    """教室/场地信息"""
    __tablename__ = "classrooms"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="教室ID")
    name = Column(String(100), unique=True, nullable=False, comment="教室名称")
    room_code = Column(String(50), unique=True, nullable=False, comment="教室编号")
    building = Column(String(100), nullable=True, comment="所在教学楼")
    floor = Column(Integer, nullable=True, comment="所在楼层")
    capacity = Column(Integer, nullable=False, default=50, comment="容纳人数")
    room_type = Column(String(30), default="普通教室", comment="教室类型: 普通教室/实验室/机房/多媒体教室/阶梯教室")
    has_multimedia = Column(Boolean, default=True, comment="是否有多媒体设备")
    is_available = Column(Boolean, default=True, comment="是否可用")
    remarks = Column(Text, nullable=True, comment="备注")

    def __repr__(self):
        return f"<Classroom(id={self.id}, name='{self.name}')>"
