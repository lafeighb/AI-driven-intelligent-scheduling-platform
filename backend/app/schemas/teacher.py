"""教师相关Pydantic模式"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class TeacherBase(BaseModel):
    """教师基础字段"""
    name: str = Field(..., min_length=1, max_length=50, description="教师姓名")
    teacher_code: str = Field(..., min_length=1, max_length=30, description="教师工号")
    department: Optional[str] = Field(None, max_length=100)
    title: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=100)
    phone: Optional[str] = Field(None, max_length=30)
    max_weekly_hours: Optional[int] = Field(default=20, ge=0, le=40)
    preferred_time_slots: Optional[str] = Field(None, description="时间偏好(JSON)")
    courses_can_teach: Optional[str] = Field(None, description="可教授课程(JSON)")
    unavailable_slots: Optional[str] = Field(None, description="不可用时段(JSON)")
    remarks: Optional[str] = None


class TeacherCreate(TeacherBase):
    """创建教师"""
    pass


class TeacherUpdate(BaseModel):
    """更新教师"""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    teacher_code: Optional[str] = Field(None, min_length=1, max_length=30)
    department: Optional[str] = None
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    max_weekly_hours: Optional[int] = Field(None, ge=0, le=40)
    preferred_time_slots: Optional[str] = None
    courses_can_teach: Optional[str] = None
    unavailable_slots: Optional[str] = None
    remarks: Optional[str] = None


class TeacherResponse(TeacherBase):
    """教师响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
