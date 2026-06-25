"""班级管理API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.class_info import ClassInfo
from app.models.schedule import ScheduleEntry
from app.models.course import Course
from app.models.teacher import Teacher
from app.schemas.class_info import ClassInfoCreate, ClassInfoUpdate, ClassInfoResponse

router = APIRouter(prefix="/api/classes", tags=["班级管理"])


@router.get("/", response_model=List[ClassInfoResponse], summary="获取班级列表")
def list_classes(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    grade: str = Query(None, description="按年级筛选"),
    search: str = Query(None, description="搜索班级名称"),
    db: Session = Depends(get_db),
):
    """获取所有班级，支持分页和筛选"""
    query = db.query(ClassInfo)
    if grade:
        query = query.filter(ClassInfo.grade == grade)
    if search:
        query = query.filter(ClassInfo.name.contains(search))
    return query.offset(skip).limit(limit).all()


# ⚠️ 重要：/{class_id}/courses 必须放在 /{class_id} 前面，否则会被后者拦截
@router.get("/{class_id}/courses", summary="查看班级课程分配")
def get_class_courses(class_id: int, version: str = Query(None), db: Session = Depends(get_db)):
    """查看某班级分配的所有课程及各课程学时（需先执行排课）"""
    cls = db.query(ClassInfo).filter(ClassInfo.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")

    query = db.query(ScheduleEntry).filter(ScheduleEntry.class_id == class_id)
    if version:
        query = query.filter(ScheduleEntry.schedule_version == version)
    entries = query.all()

    if not entries:
        return {
            "class_id": class_id, "class_name": cls.name,
            "grade": cls.grade, "department": cls.department,
            "courses": [], "total_weekly_hours": 0,
        }

    # 按课程聚合：合并同一课程的不同排课时段
    course_map = {}
    for entry in entries:
        cid = entry.course_id
        if cid not in course_map:
            course = db.query(Course).filter(Course.id == cid).first()
            course_map[cid] = {
                "course_id": cid,
                "course_name": course.name if course else "",
                "course_code": course.course_code if course else "",
                "semester_sessions": course.semester_sessions if course else 0,
                "weekly_sessions": course.weekly_sessions if course else 0,
                "hours_per_session": course.hours_per_session if course else 0,
                "total_hours": course.total_hours if course else None,
                "teachers": set(),
                "time_slots": 0,
            }
        course_map[cid]["time_slots"] += 1
        teacher = db.query(Teacher).filter(Teacher.id == entry.teacher_id).first()
        if teacher:
            course_map[cid]["teachers"].add(teacher.name)

    courses = []
    total = 0
    for cid, info in course_map.items():
        courses.append({
            "course_id": info["course_id"],
            "course_name": info["course_name"],
            "course_code": info["course_code"],
            "semester_sessions": info["semester_sessions"],
            "weekly_sessions": info["weekly_sessions"],
            "hours_per_session": info["hours_per_session"],
            "total_hours": info["total_hours"],
            "teacher_names": list(info["teachers"]),
            "time_slots": info["time_slots"],
        })
        total += info["weekly_sessions"]

    return {
        "class_id": class_id, "class_name": cls.name,
        "grade": cls.grade, "department": cls.department,
        "courses": courses, "total_weekly_hours": total,
    }


@router.get("/{class_id}", response_model=ClassInfoResponse, summary="获取班级详情")
def get_class(class_id: int, db: Session = Depends(get_db)):
    """根据ID获取班级详情"""
    cls = db.query(ClassInfo).filter(ClassInfo.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    return cls


@router.post("/", response_model=ClassInfoResponse, status_code=201, summary="创建班级")
def create_class(data: ClassInfoCreate, db: Session = Depends(get_db)):
    """手动创建新班级"""
    existing = db.query(ClassInfo).filter(ClassInfo.name == data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"班级'{data.name}'已存在")
    cls = ClassInfo(**data.model_dump())
    db.add(cls)
    db.commit()
    db.refresh(cls)
    return cls


@router.put("/{class_id}", response_model=ClassInfoResponse, summary="更新班级")
def update_class(class_id: int, data: ClassInfoUpdate, db: Session = Depends(get_db)):
    """更新班级信息"""
    cls = db.query(ClassInfo).filter(ClassInfo.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(cls, key, value)
    db.commit()
    db.refresh(cls)
    return cls


@router.delete("/{class_id}", summary="删除班级")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    """删除班级（如有排课引用则阻止删除并提示）"""
    cls = db.query(ClassInfo).filter(ClassInfo.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")

    # 检查是否被排课条目引用
    ref_count = db.query(ScheduleEntry).filter(ScheduleEntry.class_id == class_id).count()
    if ref_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"无法删除班级「{cls.name}」：该班级有 {ref_count} 条排课记录引用，请先删除相关排课方案后再操作"
        )

    db.delete(cls)
    db.commit()
    return {"ok": True, "message": f"班级「{cls.name}」已删除"}
