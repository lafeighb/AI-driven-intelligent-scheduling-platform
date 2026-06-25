"""课程管理API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.course import Course
from app.models.schedule import ScheduleEntry
from app.schemas.course import CourseCreate, CourseUpdate, CourseResponse

router = APIRouter(prefix="/api/courses", tags=["课程管理"])


@router.get("/", response_model=List[CourseResponse], summary="获取课程列表")
def list_courses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    course_type: str = Query(None),
    department: str = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Course)
    if course_type:
        query = query.filter(Course.course_type == course_type)
    if department:
        query = query.filter(Course.department == department)
    if search:
        query = query.filter(Course.name.contains(search))
    return query.offset(skip).limit(limit).all()


@router.get("/{course_id}", response_model=CourseResponse, summary="获取课程详情")
def get_course(course_id: int, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    return course


@router.post("/", response_model=CourseResponse, status_code=201, summary="创建课程")
def create_course(data: CourseCreate, db: Session = Depends(get_db)):
    existing = db.query(Course).filter(Course.course_code == data.course_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"课程编码'{data.course_code}'已存在")
    course = Course(**data.model_dump())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course


@router.put("/{course_id}", response_model=CourseResponse, summary="更新课程")
def update_course(course_id: int, data: CourseUpdate, db: Session = Depends(get_db)):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(course, key, value)
    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}", summary="删除课程")
def delete_course(course_id: int, db: Session = Depends(get_db)):
    """删除课程（如有排课引用则阻止删除并提示）"""
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="课程不存在")

    ref_count = db.query(ScheduleEntry).filter(ScheduleEntry.course_id == course_id).count()
    if ref_count > 0:
        raise HTTPException(
            status_code=409,
            detail=f"无法删除课程「{course.name}」：该课程有 {ref_count} 条排课记录引用，请先删除相关排课方案后再操作"
        )

    db.delete(course)
    db.commit()
    return {"ok": True, "message": f"课程「{course.name}」已删除"}
