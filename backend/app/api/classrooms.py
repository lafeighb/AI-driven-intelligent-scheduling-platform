"""教室管理API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.classroom import Classroom
from app.schemas.classroom import ClassroomCreate, ClassroomUpdate, ClassroomResponse

router = APIRouter(prefix="/api/classrooms", tags=["教室管理"])


@router.get("/", response_model=List[ClassroomResponse], summary="获取教室列表")
def list_classrooms(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    room_type: str = Query(None),
    building: str = Query(None),
    search: str = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Classroom)
    if room_type:
        query = query.filter(Classroom.room_type == room_type)
    if building:
        query = query.filter(Classroom.building == building)
    if search:
        query = query.filter(Classroom.name.contains(search))
    return query.offset(skip).limit(limit).all()


@router.get("/{classroom_id}", response_model=ClassroomResponse, summary="获取教室详情")
def get_classroom(classroom_id: int, db: Session = Depends(get_db)):
    room = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="教室不存在")
    return room


@router.post("/", response_model=ClassroomResponse, status_code=201, summary="创建教室")
def create_classroom(data: ClassroomCreate, db: Session = Depends(get_db)):
    existing = db.query(Classroom).filter(
        (Classroom.name == data.name) | (Classroom.room_code == data.room_code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="教室名称或编号已存在")
    room = Classroom(**data.model_dump())
    db.add(room)
    db.commit()
    db.refresh(room)
    return room


@router.put("/{classroom_id}", response_model=ClassroomResponse, summary="更新教室")
def update_classroom(classroom_id: int, data: ClassroomUpdate, db: Session = Depends(get_db)):
    room = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="教室不存在")
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(room, key, value)
    db.commit()
    db.refresh(room)
    return room


@router.delete("/{classroom_id}", status_code=204, summary="删除教室")
def delete_classroom(classroom_id: int, db: Session = Depends(get_db)):
    room = db.query(Classroom).filter(Classroom.id == classroom_id).first()
    if not room:
        raise HTTPException(status_code=404, detail="教室不存在")
    db.delete(room)
    db.commit()
