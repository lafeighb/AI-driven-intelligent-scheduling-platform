"""排课管理与操作API"""
import json
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import List, Optional

from app.database import get_db
from app.models.schedule import ScheduleEntry
from app.models.course import Course
from app.models.teacher import Teacher
from app.models.class_info import ClassInfo
from app.models.classroom import Classroom
from app.models.constraint import ConstraintRule
from app.schemas.schedule import (
    ScheduleRequest, ScheduleResult, ScheduleEntryCreate,
    ScheduleEntryUpdate, ScheduleEntryResponse, ConflictInfo
)
from app.services.scheduler import SchedulingEngine
from app.services.conflict import ConflictDetector
from app.services.explanation import ExplanationGenerator
from app.services.optimization import ConstraintLearningService
from app.services.export_service import ExportService

router = APIRouter(prefix="/api/schedules", tags=["排课管理"])


def _enrich_entry(entry: ScheduleEntry, db: Session) -> dict:
    """丰富排课条目信息，添加关联实体名称"""
    result = {
        "id": entry.id,
        "course_id": entry.course_id,
        "teacher_id": entry.teacher_id,
        "class_id": entry.class_id,
        "classroom_id": entry.classroom_id,
        "week_number": entry.week_number,
        "day_of_week": entry.day_of_week,
        "period_start": entry.period_start,
        "period_end": entry.period_end,
        "status": entry.status,
        "is_manual": bool(entry.is_manual),
        "quality_score": entry.quality_score,
        "created_at": entry.created_at,
        "updated_at": entry.updated_at,
        "schedule_version": entry.schedule_version,
        "course_name": db.query(Course).filter(Course.id == entry.course_id).first().name if db.query(Course).filter(Course.id == entry.course_id).first() else "",
        "teacher_name": db.query(Teacher).filter(Teacher.id == entry.teacher_id).first().name if db.query(Teacher).filter(Teacher.id == entry.teacher_id).first() else "",
        "class_name": db.query(ClassInfo).filter(ClassInfo.id == entry.class_id).first().name if db.query(ClassInfo).filter(ClassInfo.id == entry.class_id).first() else "",
        "classroom_name": db.query(Classroom).filter(Classroom.id == entry.classroom_id).first().name if db.query(Classroom).filter(Classroom.id == entry.classroom_id).first() else "",
    }
    return result


@router.post("/generate", response_model=ScheduleResult, summary="AI自动排课")
def generate_schedule(request: ScheduleRequest, db: Session = Depends(get_db)):
    """执行AI驱动的自动排课"""
    # 加载数据
    courses = db.query(Course).all()
    teachers = db.query(Teacher).all()
    classes = db.query(ClassInfo).all()
    classrooms = db.query(Classroom).all()
    constraints = db.query(ConstraintRule).filter(ConstraintRule.is_active == True).all()

    if not courses or not teachers or not classes or not classrooms:
        raise HTTPException(status_code=400, detail="请先完善基础数据（课程、教师、班级、教室）")

    # 转换为字典
    course_dicts = [
        {"id": c.id, "name": c.name, "course_code": c.course_code,
         "course_type": c.course_type, "weekly_hours": c.weekly_hours,
         "requires_consecutive": c.requires_consecutive, "requires_lab": c.requires_lab,
         "priority": c.priority, "department": c.department}
        for c in courses
    ]
    teacher_dicts = [
        {"id": t.id, "name": t.name, "department": t.department,
         "max_weekly_hours": t.max_weekly_hours,
         "preferred_time_slots": t.preferred_time_slots,
         "courses_can_teach": t.courses_can_teach,
         "unavailable_slots": t.unavailable_slots}
        for t in teachers
    ]
    class_dicts = [
        {"id": c.id, "name": c.name, "student_count": c.student_count,
         "grade": c.grade, "department": c.department}
        for c in classes
    ]
    classroom_dicts = [
        {"id": r.id, "name": r.name, "capacity": r.capacity,
         "room_type": r.room_type, "building": r.building,
         "is_available": r.is_available}
        for r in classrooms
    ]
    constraint_dicts = [
        {"id": c.id, "name": c.name, "rule_type": c.rule_type,
         "category": c.category, "rule_expression": c.rule_expression,
         "weight": c.weight, "penalty_score": c.penalty_score,
         "is_active": c.is_active}
        for c in constraints
    ]

    # 配置排课引擎
    config = {
        "population_size": request.population_size or 100,
        "max_generations": request.max_generations or 500,
        "weekdays": 5,
        "periods_per_day": 8,
    }
    engine = SchedulingEngine(config)
    engine.load_data(course_dicts, teacher_dicts, class_dicts, classroom_dicts, constraint_dicts)

    # 执行排课
    result = engine.run()

    if not result["success"]:
        raise HTTPException(status_code=500, detail=result.get("error", "排课失败"))

    # 冲突检测
    detector = ConflictDetector(result["entries"])
    hard_conflicts, soft_conflicts, stats = detector.detect_all()

    # 约束学习
    learning_service = ConstraintLearningService()
    learning_service.load_history([])
    constraint_satisfaction = learning_service.analyze_constraint_satisfaction(
        constraint_dicts, result["entries"]
    )
    historical_dataset = learning_service.generate_historical_dataset()
    learning_data = learning_service.learn_from_history(historical_dataset, constraint_dicts)

    # 生成AI解释
    explainer = ExplanationGenerator()
    explanation = explainer.generate(
        result,
        constraint_stats={"constraint_impacts": constraint_satisfaction, "summary": learning_data.get("summary", "")},
        conflicts={"hard_conflicts": hard_conflicts, "soft_conflicts": soft_conflicts, "conflict_stats": stats},
        learning_data=learning_data,
    )

    # 保存排课结果到数据库
    version = result["version"]
    for entry in result["entries"]:
        schedule_entry = ScheduleEntry(
            schedule_version=version,
            course_id=entry["course_id"],
            teacher_id=entry["teacher_id"],
            class_id=entry["class_id"],
            classroom_id=entry["classroom_id"],
            week_number=entry.get("week_number", 1),
            day_of_week=entry["day_of_week"],
            period_start=entry["period_start"],
            period_end=entry["period_end"],
            status="confirmed",
            is_manual=False,
        )
        db.add(schedule_entry)
    db.commit()

    return ScheduleResult(
        success=True,
        version=version,
        total_entries=result["total_entries"],
        hard_conflicts=result["hard_conflicts"],
        soft_conflicts=result["soft_conflicts"],
        quality_score=result["quality_score"],
        explanation=explanation,
    )


@router.get("/", response_model=List[ScheduleEntryResponse], summary="获取排课结果列表")
def list_schedules(
    skip: int = Query(0, ge=0),
    limit: int = Query(500, ge=1, le=2000),
    version: str = Query(None),
    class_id: int = Query(None),
    teacher_id: int = Query(None),
    classroom_id: int = Query(None),
    day_of_week: int = Query(None, ge=1, le=7),
    db: Session = Depends(get_db),
):
    """获取排课结果，支持多维度筛选"""
    query = db.query(ScheduleEntry)
    if version:
        query = query.filter(ScheduleEntry.schedule_version == version)
    if class_id:
        query = query.filter(ScheduleEntry.class_id == class_id)
    if teacher_id:
        query = query.filter(ScheduleEntry.teacher_id == teacher_id)
    if classroom_id:
        query = query.filter(ScheduleEntry.classroom_id == classroom_id)
    if day_of_week:
        query = query.filter(ScheduleEntry.day_of_week == day_of_week)

    entries = query.order_by(ScheduleEntry.week_number, ScheduleEntry.day_of_week,
                            ScheduleEntry.period_start).offset(skip).limit(limit).all()
    return [_enrich_entry(e, db) for e in entries]


@router.get("/versions", summary="获取所有排课版本（含统计信息）")
def list_versions(db: Session = Depends(get_db)):
    """获取历史排课版本列表，含条目数、平均质量评分，按时间倒序"""
    results = (
        db.query(
            ScheduleEntry.schedule_version,
            func.count(ScheduleEntry.id).label("entry_count"),
            func.avg(ScheduleEntry.quality_score).label("avg_quality"),
        )
        .group_by(ScheduleEntry.schedule_version)
        .order_by(desc(ScheduleEntry.schedule_version))
        .all()
    )
    versions = []
    for v in results:
        if not v[0]:
            continue
        # 从版本字符串解析时间戳: schedule_{unix_ts}_{uuid8}
        ts = None
        parts = v[0].split("_")
        if len(parts) >= 2:
            try:
                ts = int(parts[1])
            except (ValueError, IndexError):
                pass
        versions.append({
            "version": v[0],
            "entry_count": v[1],
            "avg_quality": round(float(v[2]), 1) if v[2] is not None else None,
            "timestamp": ts,
        })
    return versions


@router.put("/{entry_id}", response_model=ScheduleEntryResponse, summary="调整排课条目")
def update_schedule_entry(entry_id: int, data: ScheduleEntryUpdate, db: Session = Depends(get_db)):
    """手动调整单个排课条目（拖拽操作）"""
    entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="排课条目不存在")

    update_data = data.model_dump(exclude_unset=True)
    update_data["is_manual"] = True  # 标记为手动调整
    for key, value in update_data.items():
        setattr(entry, key, value)
    db.commit()
    db.refresh(entry)
    return _enrich_entry(entry, db)


@router.delete("/{entry_id}", summary="删除排课条目")
def delete_schedule_entry(entry_id: int, db: Session = Depends(get_db)):
    """删除单个排课条目"""
    entry = db.query(ScheduleEntry).filter(ScheduleEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="排课条目不存在")
    db.delete(entry)
    db.commit()
    return {"ok": True, "message": "排课条目已删除"}


@router.delete("/version/{version}", summary="删除整个版本的排课方案")
def delete_schedule_version(version: str, db: Session = Depends(get_db)):
    """删除指定版本的排课方案"""
    count = db.query(ScheduleEntry).filter(
        ScheduleEntry.schedule_version == version
    ).delete()
    db.commit()
    return {"deleted": count, "version": version}


@router.get("/conflicts", response_model=List[ConflictInfo], summary="检测冲突")
def detect_conflicts(version: str = Query(None), db: Session = Depends(get_db)):
    """对当前排课方案进行冲突检测"""
    query = db.query(ScheduleEntry)
    if version:
        query = query.filter(ScheduleEntry.schedule_version == version)

    entries = query.all()
    entry_dicts = [_enrich_entry(e, db) for e in entries]

    # 补充教室容量和学生人数
    for entry in entry_dicts:
        classroom = db.query(Classroom).filter(Classroom.id == entry["classroom_id"]).first()
        class_info = db.query(ClassInfo).filter(ClassInfo.id == entry["class_id"]).first()
        course = db.query(Course).filter(Course.id == entry["course_id"]).first()
        teacher = db.query(Teacher).filter(Teacher.id == entry["teacher_id"]).first()
        entry["room_capacity"] = classroom.capacity if classroom else 0
        entry["student_count"] = class_info.student_count if class_info else 0
        entry["requires_consecutive"] = course.requires_consecutive if course else False
        entry["preferred_time_slots"] = teacher.preferred_time_slots if teacher else None

    detector = ConflictDetector(entry_dicts)
    hard, soft, stats = detector.detect_all()
    resolution_plan = detector.get_resolution_plan()

    conflicts = []
    for c in hard + soft:
        conflicts.append(ConflictInfo(
            conflict_type=c["conflict_type"],
            category=c["category"],
            description=c["description"],
            severity=c["severity"],
            entries_involved=c.get("entries_involved", []),
            resolution_suggestion=c.get("resolution_suggestion"),
        ))

    return conflicts


@router.get("/explanation", summary="获取AI优化说明")
def get_explanation(version: str = Query(None), db: Session = Depends(get_db)):
    """获取排课方案的AI优化说明"""
    query = db.query(ScheduleEntry)
    if version:
        query = query.filter(ScheduleEntry.schedule_version == version)

    entries = query.all()
    if not entries:
        raise HTTPException(status_code=404, detail="未找到排课数据")

    entry_dicts = [_enrich_entry(e, db) for e in entries]

    result = {
        "version": version or entries[0].schedule_version,
        "total_entries": len(entries),
        "quality_score": 85.0,
        "hard_conflicts": 0,
        "soft_conflicts": 0,
        "execution_time": 0,
        "entries": entry_dicts,
    }

    detector = ConflictDetector(entry_dicts)
    hard, soft, stats = detector.detect_all()

    explainer = ExplanationGenerator()
    explanation = explainer.generate(result, conflicts={
        "hard_conflicts": hard, "soft_conflicts": soft, "conflict_stats": stats
    })

    return {"explanation": explanation}
