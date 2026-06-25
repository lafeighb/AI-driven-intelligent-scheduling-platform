"""数据导入导出API"""
import json
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
import io
from urllib.parse import quote

from app.database import get_db
from app.models.class_info import ClassInfo
from app.models.teacher import Teacher
from app.models.course import Course
from app.models.classroom import Classroom
from app.models.schedule import ScheduleEntry
from app.utils.csv_parser import parse_csv_content, generate_csv_template
from app.services.validation import ValidationService
from app.services.export_service import ExportService
from app.services.conflict import ConflictDetector
from app.services.explanation import ExplanationGenerator

router = APIRouter(prefix="/api/io", tags=["导入导出"])


@router.get("/template/{entity_type}", summary="下载CSV导入模板")
def download_template(entity_type: str):
    """下载指定实体类型的CSV导入模板"""
    content = generate_csv_template(entity_type)
    if not content:
        raise HTTPException(status_code=400, detail=f"未知的实体类型: {entity_type}")

    return StreamingResponse(
        io.BytesIO(content.encode('utf-8-sig')),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={entity_type}_template.csv"}
    )


@router.post("/csv/{entity_type}", summary="CSV批量导入")
async def import_csv(entity_type: str, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """通过CSV文件批量导入实体数据"""
    if not file.filename or not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="请上传CSV格式的文件")

    content = await file.read()
    try:
        text_content = content.decode('utf-8-sig')
    except UnicodeDecodeError:
        text_content = content.decode('gbk')

    data_rows, parse_errors = parse_csv_content(text_content, entity_type)

    if parse_errors and not data_rows:
        return {"success": False, "errors": parse_errors, "imported": 0}

    # 数据校验
    validator = ValidationService(db)
    validation_result = validator.validate_batch(entity_type, data_rows)

    if validation_result["invalid"] > 0:
        return {
            "success": False,
            "imported": validation_result["valid"],
            "errors": [e["message"] for e in validation_result["errors"]],
            "warnings": [w["message"] for w in validation_result["warnings"]],
            "summary": validation_result["summary"],
        }

    # 批量存入数据库
    model_map = {
        "classes": ClassInfo,
        "teachers": Teacher,
        "courses": Course,
        "classrooms": Classroom,
    }
    model_class = model_map.get(entity_type)
    if not model_class:
        raise HTTPException(status_code=400, detail=f"未知实体类型: {entity_type}")

    imported_count = 0
    import_errors = []
    for row in data_rows:
        try:
            obj = model_class(**row)
            db.add(obj)
            imported_count += 1
        except Exception as e:
            import_errors.append(str(e))

    db.commit()

    return {
        "success": len(import_errors) == 0,
        "imported": imported_count,
        "total": len(data_rows),
        "errors": import_errors + [e["message"] for e in parse_errors if isinstance(e, dict)],
        "warnings": [w["message"] for w in validation_result.get("warnings", [])],
        "summary": f"成功导入{imported_count}条记录" + (f"，{len(import_errors)}条失败" if import_errors else ""),
    }


@router.get("/export/excel", summary="导出Excel课表")
def export_excel(version: str = Query(None), db: Session = Depends(get_db)):
    """导出排课方案为Excel文件"""
    query = db.query(ScheduleEntry)
    if version:
        query = query.filter(ScheduleEntry.schedule_version == version)

    entries = query.all()
    if not entries:
        raise HTTPException(status_code=404, detail="未找到排课数据")

    entry_dicts = []
    for entry in entries:
        course = db.query(Course).filter(Course.id == entry.course_id).first()
        teacher = db.query(Teacher).filter(Teacher.id == entry.teacher_id).first()
        cls = db.query(ClassInfo).filter(ClassInfo.id == entry.class_id).first()
        room = db.query(Classroom).filter(Classroom.id == entry.classroom_id).first()

        entry_dicts.append({
            "course_name": course.name if course else "",
            "teacher_name": teacher.name if teacher else "",
            "class_name": cls.name if cls else "",
            "classroom_name": room.name if room else "",
            "week_number": entry.week_number,
            "day_of_week": entry.day_of_week,
            "period_start": entry.period_start,
            "period_end": entry.period_end,
            "is_consecutive": entry.period_end > entry.period_start,
            "status": entry.status,
        })

    metadata = {
        "version": version or entries[0].schedule_version,
        "total_entries": len(entries),
        "generated_at": "",
    }
    excel_bytes = ExportService.export_to_excel(entry_dicts, metadata)

    filename_base = f"排课方案_{version or 'latest'}"
    filename_ascii = f"scheduling_{version or 'latest'}.xlsx"
    filename_utf8 = f"{filename_base}.xlsx"
    encoded_filename = quote(filename_utf8)
    return StreamingResponse(
        io.BytesIO(excel_bytes),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename_ascii}\"; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get("/export/pdf", summary="导出PDF课表")
def export_pdf(version: str = Query(None), view_type: str = Query("class"),
               db: Session = Depends(get_db)):
    """导出排课方案为PDF格式"""
    query = db.query(ScheduleEntry)
    if version:
        query = query.filter(ScheduleEntry.schedule_version == version)

    entries = query.all()
    if not entries:
        raise HTTPException(status_code=404, detail="未找到排课数据")

    entry_dicts = []
    for entry in entries:
        course = db.query(Course).filter(Course.id == entry.course_id).first()
        teacher = db.query(Teacher).filter(Teacher.id == entry.teacher_id).first()
        cls = db.query(ClassInfo).filter(ClassInfo.id == entry.class_id).first()
        room = db.query(Classroom).filter(Classroom.id == entry.classroom_id).first()

        entry_dicts.append({
            "course_name": course.name if course else "",
            "teacher_name": teacher.name if teacher else "",
            "class_name": cls.name if cls else "",
            "classroom_name": room.name if room else "",
            "week_number": entry.week_number,
            "day_of_week": entry.day_of_week,
            "period_start": entry.period_start,
            "period_end": entry.period_end,
            "is_consecutive": entry.period_end > entry.period_start,
        })

    metadata = {"version": version or entries[0].schedule_version, "total_entries": len(entries)}
    pdf_bytes = ExportService.export_to_pdf(entry_dicts, metadata, view_type)

    filename_view = {"class": "班级", "teacher": "教师", "classroom": "教室"}.get(view_type, view_type)
    filename_base = f"排课方案_{filename_view}视图"
    filename_ascii = f"scheduling_{view_type}.pdf"
    filename_utf8 = f"{filename_base}.pdf"
    encoded_filename = quote(filename_utf8)
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=\"{filename_ascii}\"; filename*=UTF-8''{encoded_filename}"
        }
    )


@router.get("/report", summary="生成智能分析报告")
def generate_report(version: str = Query(None), db: Session = Depends(get_db)):
    """生成排课方案的智能分析报告"""
    query = db.query(ScheduleEntry)
    if version:
        query = query.filter(ScheduleEntry.schedule_version == version)

    entries = query.all()
    if not entries:
        raise HTTPException(status_code=404, detail="未找到排课数据")

    entry_dicts = []
    for entry in entries:
        course = db.query(Course).filter(Course.id == entry.course_id).first()
        teacher = db.query(Teacher).filter(Teacher.id == entry.teacher_id).first()
        cls = db.query(ClassInfo).filter(ClassInfo.id == entry.class_id).first()
        room = db.query(Classroom).filter(Classroom.id == entry.classroom_id).first()
        entry_dicts.append({
            "id": entry.id, "course_id": entry.course_id, "teacher_id": entry.teacher_id,
            "class_id": entry.class_id, "classroom_id": entry.classroom_id,
            "week_number": entry.week_number, "day_of_week": entry.day_of_week,
            "period_start": entry.period_start, "period_end": entry.period_end,
            "course_name": course.name if course else "",
            "teacher_name": teacher.name if teacher else "",
            "class_name": cls.name if cls else "",
            "classroom_name": room.name if room else "",
            "student_count": cls.student_count if cls else 0,
            "room_capacity": room.capacity if room else 0,
        })

    # 冲突检测
    detector = ConflictDetector(entry_dicts)
    hard, soft, stats = detector.detect_all()

    # AI解释
    explainer = ExplanationGenerator()
    schedule_result = {
        "version": version or entries[0].schedule_version,
        "total_entries": len(entries),
        "quality_score": 85.0,
        "hard_conflicts": len(hard),
        "soft_conflicts": len(soft),
        "execution_time": 0,
        "entries": entry_dicts,
    }
    explanation = explainer.generate(schedule_result, conflicts={
        "hard_conflicts": hard, "soft_conflicts": soft, "conflict_stats": stats
    })

    # 生成完整报告
    report = ExportService.generate_analysis_report(
        schedule_result,
        {"hard_conflicts": hard, "soft_conflicts": soft, "conflict_stats": stats},
        explanation,
    )

    return report
