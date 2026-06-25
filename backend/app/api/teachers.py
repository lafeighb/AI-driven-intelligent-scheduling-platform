"""教师管理API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.teacher import Teacher
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


@router.delete("/{teacher_id}", status_code=204, summary="删除教师")
def delete_teacher(teacher_id: int, db: Session = Depends(get_db)):
    teacher = db.query(Teacher).filter(Teacher.id == teacher_id).first()
    if not teacher:
        raise HTTPException(status_code=404, detail="教师不存在")
    db.delete(teacher)
    db.commit()
