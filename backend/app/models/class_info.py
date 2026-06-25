"""班级数据模型"""
from sqlalchemy import Column, Integer, String, Text, DateTime, func
from app.database import Base
from app.models.base import TimestampMixin


class ClassInfo(Base, TimestampMixin):
    """班级信息"""
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="班级ID")
    name = Column(String(100), unique=True, nullable=False, comment="班级名称，如'高一(1)班'")
    grade = Column(String(20), nullable=False, comment="年级，如'高一'")
    student_count = Column(Integer, nullable=False, default=0, comment="学生人数")
    department = Column(String(100), nullable=True, comment="所属系/专业")
    homeroom_teacher = Column(String(50), nullable=True, comment="班主任姓名")
    remarks = Column(Text, nullable=True, comment="备注信息")

    def __repr__(self):
        return f"<ClassInfo(id={self.id}, name='{self.name}')>"
