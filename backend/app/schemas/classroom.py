"""教室相关Pydantic模式"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ClassroomBase(BaseModel):
    """教室基础字段"""
    name: str = Field(..., min_length=1, max_length=100, description="教室名称")
    room_code: str = Field(..., min_length=1, max_length=50, description="教室编号")
    building: Optional[str] = Field(None, max_length=100)
    floor: Optional[int] = Field(None, ge=0)
    capacity: int = Field(default=50, ge=1, description="容纳人数")
    room_type: str = Field(default="普通教室", description="教室类型")
    has_multimedia: bool = Field(default=True)
    is_available: bool = Field(default=True)
    remarks: Optional[str] = None


class ClassroomCreate(ClassroomBase):
    """创建教室"""
    pass


class ClassroomUpdate(BaseModel):
    """更新教室"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    room_code: Optional[str] = Field(None, min_length=1, max_length=50)
    building: Optional[str] = None
    floor: Optional[int] = Field(None, ge=0)
    capacity: Optional[int] = Field(None, ge=1)
    room_type: Optional[str] = None
    has_multimedia: Optional[bool] = None
    is_available: Optional[bool] = None
    remarks: Optional[str] = None


class ClassroomResponse(ClassroomBase):
    """教室响应"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
