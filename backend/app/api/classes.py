"""班级管理API"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.class_info import ClassInfo
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


@router.delete("/{class_id}", status_code=204, summary="删除班级")
def delete_class(class_id: int, db: Session = Depends(get_db)):
    """删除班级"""
    cls = db.query(ClassInfo).filter(ClassInfo.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="班级不存在")
    db.delete(cls)
    db.commit()
