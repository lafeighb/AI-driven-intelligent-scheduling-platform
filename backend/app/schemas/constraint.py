"""约束规则相关Pydantic模式"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ConstraintRuleBase(BaseModel):
    """约束规则基础字段"""
    name: str = Field(..., min_length=1, max_length=200, description="规则名称")
    description: Optional[str] = None
    rule_type: str = Field(..., pattern="^(hard|soft)$", description="约束类型: hard/soft")
    category: str = Field(..., description="约束分类: teacher/classroom/class/course/time")
    rule_expression: Optional[str] = Field(None, description="规则表达式(JSON)")
    weight: float = Field(default=1.0, ge=0, le=10, description="权重")
    penalty_score: float = Field(default=10.0, ge=0, description="惩罚分数")
    is_active: bool = True
    priority: int = Field(default=5, ge=0, le=10)


class ConstraintRuleCreate(ConstraintRuleBase):
    """创建约束规则"""
    pass


class ConstraintRuleUpdate(BaseModel):
    """更新约束规则"""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    rule_type: Optional[str] = Field(None, pattern="^(hard|soft)$")
    category: Optional[str] = None
    rule_expression: Optional[str] = None
    weight: Optional[float] = Field(None, ge=0, le=10)
    penalty_score: Optional[float] = Field(None, ge=0)
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=10)


class ConstraintRuleResponse(ConstraintRuleBase):
    """约束规则响应"""
    id: int
    learned_from_history: bool
    satisfaction_rate: Optional[float]
    conflict_severity: Optional[float]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ConstraintLearningResult(BaseModel):
    """约束学习分析结果"""
    rule_id: int
    rule_name: str
    satisfaction_rate: float
    conflict_count: int
    conflict_severity_mean: float
    impact_on_quality: float
    recommendation: str
