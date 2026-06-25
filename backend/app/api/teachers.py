"""教师管理API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.teacher import Teacher
from app.models.schedule import ScheduleEntry
from app.models.course import Course
from app.models.class_info import ClassInfo
from app.schemas.teacher import TeacherCreate, TeacherUpdate, TeacherResponse

router = APIRouter(prefix="/api/teachers", tags=["教师管理"])


@router.get("/", response_model=List[TeacherResponse], summary="获取教师列表")
def list_teachers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    department: str = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
):
    """获取所有教师"""
    query = db.query(Teacher)
    if department:
        query = query.filter(Teacher.department == department)
    if search:
        query = query.filter(Teacher.name.contains(search))
    return query.offset(skip).limit(limit).all()


# ⚠️ 重要：/{teacher_id}/courses 必须放在 /{teacher_id} 前面，否则会被后者拦截
@router.get("/{teacher_id}/courses", summary="查看教师课程分配")
def get_teacher_courses(teacher_id: int, version: str = Query(None), db: Session = Depends(get_db)):
    """查看某教师分配的所有课程及各课程学时（需先执行排课）"""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")

    query = db.query(ScheduleEntry).filter(ScheduleEntry.teacher_id == teacher_id)
    if version:
        query = query.filter(ScheduleEntry.schedule_version == version)
    entries = query.all()

    if not entries:
        return {
            "teacher_id": teacher_id, "teacher_name": teacher.name,
            "department": teacher.department, "title": teacher.title,
            "courses": [], "total_weekly_hours": 0,
        }

    # 按课程+班级聚合
    course_map = {}
    for entry in entries:
        key = (entry.course_id, entry.class_id)
        if key not in course_map:
            course = db.query(Course).filter(Course.id == entry.course_id).first()
            cls = db.query(ClassInfo).filter(ClassInfo.id == entry.class_id).first()
            course_map[key] = {
                "course_id": entry.course_id,
                "course_name": course.name if course else "",
                "course_code": course.course_code if course else "",
                "semester_sessions": course.semester_sessions if course else 0,
                "weekly_sessions": course.weekly_sessions if course else 0,
                "hours_per_session": course.hours_per_session if course else 0,
                "total_hours": course.total_hours if course else None,
                "class_name": cls.name if cls else "",
                "time_slots": 0,
            }
        course_map[key]["time_slots"] += 1

    courses = []
    total = 0
    for key, info in course_map.items():
        courses.append({
            "course_id": info["course_id"],
            "course_name": info["course_name"],
            "course_code": info["course_code"],
            "semester_sessions": info["semester_sessions"],
            "weekly_sessions": info["weekly_sessions"],
            "hours_per_session": info["hours_per_session"],
            "total_hours": info["total_hours"],
            "class_name": info["class_name"],
            "time_slots": info["time_slots"],
        })
        total += info["weekly_sessions"]

    return {
        "teacher_id": teacher_id, "teacher_name": teacher.name,
        "department": teacher.department, "title": teacher.title,
        "courses": courses, "total_weekly_hours": total,
    }


@router.get("/{teacher_id}", response_model=TeacherResponse, summary="获取教师详情")
def get_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    return teacher


@router.post("/", response_model=TeacherResponse, status_code=201, summary="创建教师")
def create_teacher(data: TeacherCreate, db: Session = Depends(get_db)):
    existing = db.query(Teacher).filter(
        (Teacher.teacher_code == data.teacher_code) | (Teacher.email == data.email)
    ).first() if data.email else db.query(Teacher).filter(
        Teacher.teacher_code == data.teacher_code
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="教师工号或邮箱已存在")
    teacher = Teacher(**data.model_dump())
    db.add(teacher)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.put("/{teacher_id}", response_model=TeacherResponse, summary="更新教师")
def update_teacher(teacher_id: int, data: TeacherUpdate, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(teacher, key, value)
    db.commit()
    db.refresh(teacher)
    return teacher


@router.delete("/{teacher_id}", summary="删除教师")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    """删除教师（如有排课引用则阻止删除并提示）"""
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")

    ref_count = db.query(ScheduleEntry).filter(ScheduleEntry.teacher_id == teacher_id).count()
    if ref_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"无法删除教师「{teacher.name}」：该教师有 {ref_count} 条排课记录引用，请先删除相关排课方案后再操作"
        )

    db.delete(teacher)
    db.commit()
    return {"ok": True, "message": f"教师「{teacher.name}」已删除"}
