"""排课相关Pydantic模式"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ScheduleEntryBase(BaseModel):
    """排课条目基础字段"""
    course_id: int = Field(..., description="课程ID")
    teacher_id: int = Field(..., description="教师ID")
    class_id: int = Field(..., description="班级ID")
    classroom_id: int = Field(..., description="教室ID")
    week_number: int = Field(..., ge=1, le=30, description="教学周次")
    day_of_week: int = Field(..., ge=1, le=7, description="星期几")
    period_start: int = Field(..., ge=1, le=12, description="开始节次")
    period_end: int = Field(..., ge=1, le=12, description="结束节次")


class ScheduleEntryCreate(ScheduleEntryBase):
    """创建排课条目"""
    status: str = "confirmed"
    is_manual: bool = False


class ScheduleEntryUpdate(BaseModel):
    """更新排课条目"""
    teacher_id: Optional[int] = None
    classroom_id: Optional[int] = None
    week_number: Optional[int] = Field(None, ge=1, le=30)
    day_of_week: Optional[int] = Field(None, ge=1, le=7)
    period_start: Optional[int] = Field(None, ge=1, le=12)
    period_end: Optional[int] = Field(None, ge=1, le=12)
    status: Optional[str] = None


class ScheduleEntryResponse(ScheduleEntryBase):
    """排课条目响应"""
    id: int
    schedule_version: Optional[str]
    status: str
    is_manual: bool
    quality_score: Optional[float]
    created_at: datetime
    updated_at: datetime

    # 关联实体名称（便于前端展示）
    course_name: Optional[str] = None
    teacher_name: Optional[str] = None
    class_name: Optional[str] = None
    classroom_name: Optional[str] = None

    model_config = {"from_attributes": True}


class ScheduleRequest(BaseModel):
    """排课请求参数"""
    schedule_version: Optional[str] = None
    class_ids: Optional[List[int]] = None
    teacher_ids: Optional[List[int]] = None
    course_ids: Optional[List[int]] = None
    week_range: Optional[List[int]] = Field(None, description="教学周范围[start, end]")
    algorithm: str = Field(default="genetic", description="排课算法: genetic/greedy/hybrid")
    population_size: Optional[int] = Field(None, ge=50, le=500)
    max_generations: Optional[int] = Field(None, ge=100, le=2000)


class ScheduleResult(BaseModel):
    """排课结果"""
    success: bool
    version: str
    total_entries: int
    hard_conflicts: int
    soft_conflicts: int
    quality_score: float
    explanation: str
    entries: List[ScheduleEntryResponse] = []


class ConflictInfo(BaseModel):
    """冲突信息"""
    conflict_type: str  # hard/soft
    category: str  # teacher/classroom/class/course/time
    description: str
    severity: float  # 0-10
    entries_involved: List[int] = []  # 涉及的排课条目ID
    resolution_suggestion: Optional[str] = None
