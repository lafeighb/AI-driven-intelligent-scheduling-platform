"""课程相关Pydantic模式"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CourseBase(BaseModel):
    """课程基础字段"""
    name: str = Field(..., min_length=1, max_length=200, description="课程名称")
    course_code: str = Field(..., min_length=1, max_length=50, description="课程编码")
    course_type: str = Field(default="必修", description="课程类型")
    weekly_hours: int = Field(default=2, ge=1, le=8, description="每周课时数")
    total_hours: Optional[int] = Field(None, ge=1)
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
    weekly_hours: Optional[int] = Field(None, ge=1, le=8)
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
