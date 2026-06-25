"""排课结果数据模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Float
from app.database import Base
from app.models.base import TimestampMixin


class ScheduleEntry(Base, TimestampMixin):
    """排课条目 - 表示一节具体的课程安排"""
    __tablename__ = "schedule_entries"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="排课条目ID")
    schedule_version = Column(String(50), nullable=True, comment="排课版本号")

    # 关联实体ID
    course_id = Column(Integer, ForeignKey("courses.id"), nullable=False, comment="课程ID")
    teacher_id = Column(Integer, ForeignKey("teachers.id"), nullable=False, comment="教师ID")
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False, comment="班级ID")
    classroom_id = Column(Integer, ForeignKey("classrooms.id"), nullable=False, comment="教室ID")

    # 时间信息
    week_number = Column(Integer, nullable=False, comment="教学周次(从1开始)")
    day_of_week = Column(Integer, nullable=False, comment="星期几(1=周一,5=周五)")
    period_start = Column(Integer, nullable=False, comment="开始节次(1-8)")
    period_end = Column(Integer, nullable=False, comment="结束节次(1-8)")

    # 状态信息
    status = Column(String(20), default="confirmed", comment="状态: draft/confirmed/manual")
    is_manual = Column(Integer, default=0, comment="是否手动调整")

    # 质量评分
    quality_score = Column(Float, nullable=True, comment="该条目的质量评分(0-100)")

    # 备注
    remarks = Column(Text, nullable=True, comment="备注")

    def __repr__(self):
        return (f"<ScheduleEntry(course={self.course_id}, teacher={self.teacher_id}, "
                f"class={self.class_id}, room={self.classroom_id}, "
                f"W{self.week_number}-D{self.day_of_week}-P{self.period_start})>")
