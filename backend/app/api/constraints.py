"""约束规则管理API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.constraint import ConstraintRule
from app.schemas.constraint import (
    ConstraintRuleCreate, ConstraintRuleUpdate,
    ConstraintRuleResponse, ConstraintLearningResult
)
from app.services.optimization import ConstraintLearningService

router = APIRouter(prefix="/api/constraints", tags=["约束管理"])


@router.get("/", response_model=List[ConstraintRuleResponse], summary="获取约束规则列表")
def list_constraints(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1),
    rule_type: str = Query(None, description="hard/soft"),
    category: str = Query(None),
    is_active: bool = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(ConstraintRule)
    if rule_type:
        query = query.filter(ConstraintRule.rule_type == rule_type)
    if category:
        query = query.filter(ConstraintRule.category == category)
    if is_active is not None:
        query = query.filter(ConstraintRule.is_active == is_active)
    return query.order_by(ConstraintRule.priority.desc()).offset(skip).limit(limit).all()


@router.get("/defaults", summary="获取默认约束规则")
def get_default_constraints():
    """获取系统预置的默认约束规则"""
    defaults = [
        {"name": "教师时间不冲突", "rule_type": "hard", "category": "teacher",
         "description": "同一教师在同一时间只能教授一门课程",
         "weight": 10.0, "penalty_score": 100.0, "priority": 10,
         "rule_expression": '{"type": "unique", "fields": ["teacher_id", "day_of_week", "period_start"]}'},

        {"name": "教室不重复占用", "rule_type": "hard", "category": "classroom",
         "description": "同一教室在同一时间只能被一个班级使用",
         "weight": 10.0, "penalty_score": 100.0, "priority": 10,
         "rule_expression": '{"type": "unique", "fields": ["classroom_id", "day_of_week", "period_start"]}'},

        {"name": "班级课程不冲突", "rule_type": "hard", "category": "class",
         "description": "同一班级在同一时间只能上一门课程",
         "weight": 10.0, "penalty_score": 100.0, "priority": 10,
         "rule_expression": '{"type": "unique", "fields": ["class_id", "day_of_week", "period_start"]}'},

        {"name": "教室容量匹配", "rule_type": "hard", "category": "classroom",
         "description": "教室容量应不小于上课班级的学生人数",
         "weight": 8.0, "penalty_score": 50.0, "priority": 8,
         "rule_expression": '{"type": "compare", "field1": "room_capacity", "field2": "student_count", "op": "gte"}'},

        {"name": "教师时间偏好", "rule_type": "soft", "category": "teacher",
         "description": "尽量满足教师的时间偏好设置",
         "weight": 5.0, "penalty_score": 5.0, "priority": 5,
         "rule_expression": '{"type": "preference", "field": "preferred_time_slots"}'},

        {"name": "课时均匀分布", "rule_type": "soft", "category": "time",
         "description": "同一课程在一周内应尽量均匀分布，避免集中在某一天",
         "weight": 4.0, "penalty_score": 3.0, "priority": 4,
         "rule_expression": '{"type": "distribution", "max_per_day": 2}'},

        {"name": "连排课程要求", "rule_type": "soft", "category": "course",
         "description": "需要连排的课程应安排在连续的两个节次",
         "weight": 6.0, "penalty_score": 8.0, "priority": 6,
         "rule_expression": '{"type": "consecutive", "min_gap": 0}'},

        {"name": "班级日课时均衡", "rule_type": "soft", "category": "class",
         "description": "每个班级每日的课时数应尽量均衡",
         "weight": 3.0, "penalty_score": 2.0, "priority": 3,
         "rule_expression": '{"type": "balance", "field": "class_id", "group_by": "day_of_week"}'},
    ]
    return {"defaults": defaults}


@router.get("/{rule_id}", response_model=ConstraintRuleResponse, summary="获取约束详情")
def get_constraint(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(ConstraintRule).filter(ConstraintRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="约束规则不存在")
    return rule


@router.post("/", response_model=ConstraintRuleResponse, status_code=201, summary="创建约束规则")
def create_constraint(data: ConstraintRuleCreate, db: Session = Depends(get_db)):
    rule = ConstraintRule(**data.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/{rule_id}", response_model=ConstraintRuleResponse, summary="更新约束规则")
def update_constraint(rule_id: int, data: ConstraintRuleUpdate, db: Session = Depends(get_db)):
    rule = db.query(ConstraintRule).filter(ConstraintRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="约束规则不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}", status_code=204, summary="删除约束规则")
def delete_constraint(rule_id: int, db: Session = Depends(get_db)):
    rule = db.query(ConstraintRule).filter(ConstraintRule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="约束规则不存在")
    db.delete(rule)
    db.commit()


@router.post("/learn", response_model=List[ConstraintLearningResult], summary="执行约束自学习")
def learn_constraints(db: Session = Depends(get_db)):
    """基于历史数据执行约束自学习分析"""
    constraints = db.query(ConstraintRule).all()

    learning_service = ConstraintLearningService()
    historical_data = learning_service.generate_historical_dataset()
    learning_results = learning_service.learn_from_history(historical_data,
        [{"id": c.id, "name": c.name, "rule_type": c.rule_type,
          "category": c.category, "weight": c.weight} for c in constraints])

    results = []
    for impact in learning_results.get("constraint_impacts", []):
        results.append(ConstraintLearningResult(
            rule_id=impact.get("rule_id", 0) if isinstance(impact.get("rule_id"), int) else 0,
            rule_name=impact.get("rule_id", ""),
            satisfaction_rate=1.0 - min(1.0, impact.get("avg_violations", 0) / 20),
            conflict_count=int(impact.get("avg_violations", 0) * 20),
            conflict_severity_mean=min(10.0, impact.get("avg_violations", 0) * 2),
            impact_on_quality=impact.get("impact_on_quality", 0),
            recommendation=impact.get("recommendation", ""),
        ))

    return results
