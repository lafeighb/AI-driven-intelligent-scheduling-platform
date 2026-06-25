"""课程相关Pydantic模式"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CourseBase(BaseModel):
    """课程基础字段"""
    name: str = Field(..., min_length=1, max_length=200, description="课程名称")
    course_code: str = Field(..., min_length=1, max_length=50, description="课程编码")
    course_type: str = Field(default="必修", description="课程类型")
    semester_sessions: int = Field(default=16, ge=1, le=40, description="学期教学次数")
    weekly_sessions: int = Field(default=1, ge=1, le=8, description="每周上课次数")
    hours_per_session: int = Field(default=2, ge=1, le=6, description="每次课时数(1次课=几学时)")
    total_hours: Optional[int] = Field(None, ge=1, description="总课时数")
    credits: Optional[int] = Field(default=2, ge=0)
    requires_consecutive: bool = Field(default=False, description="是否需要连排")
    requires_lab: bool = Field(default=False, description="是否需要实验室")
    priority: int = Field(default=0, ge=0, le=10, description="优先级")
    department: Optional[str] = Field(None, max_length=100)
    remarks: Optional[str] = None


class CourseCreate(CourseBase):
    """创建课程"""
    pass


class CourseUpdate(BaseModel):
    """更新课程"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    course_code: Optional[str] = Field(None, min_length=1, max_length=50)
    course_type: Optional[str] = None
    semester_sessions: Optional[int] = Field(None, ge=1, le=40)
    weekly_sessions: Optional[int] = Field(None, ge=1, le=8)
    hours_per_session: Optional[int] = Field(None, ge=1, le=6)
    total_hours: Optional[int] = Field(None, ge=1)
    credits: Optional[int] = Field(None, ge=0)
    requires_consecutive: Optional[bool] = None
    requires_lab: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=10)
    department: Optional[str] = None
    remarks: Optional[str] = None


class CourseResponse(CourseBase):
    """课程响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
