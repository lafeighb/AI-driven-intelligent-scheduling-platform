"""教师数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base
from app.models.base import TimestampMixin


class Teacher(Base, TimestampMixin):
    """教师信息"""
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="教师ID")
    name = Column(String(50), nullable=False, comment="教师姓名")
    teacher_code = Column(String(30), unique=True, nullable=False, comment="教师工号")
    department = Column(String(100), nullable=True, comment="所属部门/教研组")
    title = Column(String(50), nullable=True, comment="职称")
    email = Column(String(100), nullable=True, comment="电子邮箱")
    phone = Column(String(30), nullable=True, comment="联系电话")
    max_weekly_hours = Column(Integer, nullable=True, default=20, comment="每周最大课时数")
    preferred_time_slots = Column(Text, nullable=True, comment="时间偏好(JSON格式)")
    courses_can_teach = Column(Text, nullable=True, comment="可教授课程列表(JSON格式)")
    unavailable_slots = Column(Text, nullable=True, comment="不可用时间段(JSON格式)")
    remarks = Column(Text, nullable=True, comment="备注")

    def __repr__(self):
        return f"<Teacher(id={self.id}, name='{self.name}')>"
