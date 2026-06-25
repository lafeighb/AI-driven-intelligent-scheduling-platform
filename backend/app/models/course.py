"""课程数据模型"""
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, func
from app.database import Base
from app.models.base import TimestampMixin


class Course(Base, TimestampMixin):
    """课程信息"""
    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="课程ID")
    name = Column(String(200), nullable=False, comment="课程名称")
    course_code = Column(String(50), unique=True, nullable=False, comment="课程编码")
    course_type = Column(String(30), default="必修", comment="课程类型: 必修/选修/公共课")
    weekly_hours = Column(Integer, nullable=False, default=2, comment="每周课时数")
    total_hours = Column(Integer, nullable=True, comment="总课时数")
    credits = Column(Integer, nullable=True, default=2, comment="学分")
    requires_consecutive = Column(Boolean, default=False, comment="是否需要连排(连续两节)")
    requires_lab = Column(Boolean, default=False, comment="是否需要实验室/机房")
    priority = Column(Integer, default=0, comment="优先级(0-10,越大越优先)")
    department = Column(String(100), nullable=True, comment="开课部门")
    remarks = Column(Text, nullable=True, comment="备注/课程描述")

    def __repr__(self):
        return f"<Course(id={self.id}, name='{self.name}')>"
