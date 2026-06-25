"""约束规则数据模型"""
from sqlalchemy import Column, Integer, String, Text, Float, Boolean, DateTime, func
from app.database import Base
from app.models.base import TimestampMixin


class ConstraintRule(Base, TimestampMixin):
    """排课约束规则"""
    __tablename__ = "constraint_rules"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="规则ID")
    name = Column(String(200), nullable=False, comment="规则名称")
    description = Column(Text, nullable=True, comment="规则描述")
    rule_type = Column(String(20), nullable=False, comment="约束类型: hard(硬约束)/soft(软约束)")
    category = Column(String(50), nullable=False, comment="约束分类: teacher/classroom/class/course/time")
    rule_expression = Column(Text, nullable=True, comment="规则表达式(JSON格式)")

    # 权重与惩罚
    weight = Column(Float, default=1.0, comment="软约束权重(0-10)")
    penalty_score = Column(Float, default=10.0, comment="违反惩罚分数(用于优化目标函数)")

    is_active = Column(Boolean, default=True, comment="是否启用")
    priority = Column(Integer, default=5, comment="优先级(0-10)")

    # 自学习相关
    learned_from_history = Column(Boolean, default=False, comment="是否从历史数据学习得出")
    satisfaction_rate = Column(Float, nullable=True, comment="历史满足率(0-1)")
    conflict_severity = Column(Float, nullable=True, comment="平均冲突严重程度(0-10)")

    def __repr__(self):
        return f"<ConstraintRule(id={self.id}, name='{self.name}', type='{self.rule_type}')>"
