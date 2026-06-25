"""CSV模板解析工具 - 支持批量导入排课实体数据"""
import csv
import io
from typing import List, Dict, Any, Tuple


# CSV模板字段映射定义
CSV_TEMPLATES = {
    "classes": {
        "required_fields": ["name", "grade"],
        "optional_fields": ["student_count", "department", "homeroom_teacher", "remarks"],
        "field_names": {
            "name": "班级名称",
            "grade": "年级",
            "student_count": "学生人数",
            "department": "所属专业",
            "homeroom_teacher": "班主任",
            "remarks": "备注",
        }
    },
    "teachers": {
        "required_fields": ["name", "teacher_code"],
        "optional_fields": ["department", "title", "email", "phone", "max_weekly_hours", "remarks"],
        "field_names": {
            "name": "姓名",
            "teacher_code": "工号",
            "department": "所属部门",
            "title": "职称",
            "email": "邮箱",
            "phone": "电话",
            "max_weekly_hours": "每周最大课时",
            "remarks": "备注",
        }
    },
    "courses": {
        "required_fields": ["name", "course_code", "weekly_hours"],
        "optional_fields": ["course_type", "total_hours", "credits", "requires_consecutive",
                          "requires_lab", "priority", "department", "remarks"],
        "field_names": {
            "name": "课程名称",
            "course_code": "课程编码",
            "course_type": "课程类型",
            "weekly_hours": "每周课时",
            "total_hours": "总课时",
            "credits": "学分",
            "requires_consecutive": "需连排",
            "requires_lab": "需实验室",
            "priority": "优先级",
            "department": "所属专业",
            "remarks": "备注",
        }
    },
    "classrooms": {
        "required_fields": ["name", "room_code", "capacity"],
        "optional_fields": ["building", "floor", "room_type", "has_multimedia", "remarks"],
        "field_names": {
            "name": "教室名称",
            "room_code": "教室编号",
            "building": "教学楼",
            "floor": "楼层",
            "capacity": "容量",
            "room_type": "教室类型",
            "has_multimedia": "多媒体",
            "remarks": "备注",
        }
    },
    # 课程大纲模板 — 一体化定义班级+课程+课时对照关系
    "syllabus": {
        "required_fields": ["class_name", "class_grade", "course_name", "course_code", "weekly_hours"],
        "optional_fields": ["student_count", "department", "total_hours", "credits",
                          "course_type", "requires_consecutive", "requires_lab", "priority"],
        "field_names": {
            "class_name": "班级名称",
            "class_grade": "年级",
            "student_count": "学生人数",
            "department": "所属专业",
            "course_name": "课程名称",
            "course_code": "课程编码",
            "course_type": "课程类型",
            "weekly_hours": "每周课时",
            "total_hours": "总课时",
            "credits": "学分",
            "requires_consecutive": "需连排",
            "requires_lab": "需实验室",
            "priority": "优先级",
        }
    }
}


def parse_csv_content(content: str, entity_type: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """解析CSV内容

    Args:
        content: CSV文件内容（字符串）
        entity_type: 实体类型 (classes/teachers/courses/classrooms)

    Returns:
        (parsed_data, errors) - 解析成功的数据行和错误信息列表
    """
    if entity_type not in CSV_TEMPLATES:
        return [], [f"未知的实体类型: {entity_type}"]

    template = CSV_TEMPLATES[entity_type]
    required_fields = template["required_fields"]
    all_fields = required_fields + template["optional_fields"]

    data_rows = []
    errors = []

    try:
        reader = csv.DictReader(io.StringIO(content))

        # 检查CSV表头
        if reader.fieldnames is None:
            return [], ["CSV文件为空或格式错误"]

        # 创建中文表头到英文字段的映射
        header_map = {}
        field_name_map = template["field_names"]

        for header in reader.fieldnames:
            header = header.strip()
            found = False
            for eng_field, chinese_name in field_name_map.items():
                if header == chinese_name or header == eng_field:
                    header_map[header] = eng_field
                    found = True
                    break
            if not found:
                errors.append(f"警告: 无法识别的列名 '{header}'，已忽略")

        # 检查必填字段是否存在
        mapped_fields = set(header_map.values())
        missing_required = [f for f in required_fields if f not in mapped_fields]
        if missing_required:
            missing_names = [field_name_map.get(f, f) for f in missing_required]
            return [], [f"缺少必填字段: {', '.join(missing_names)}"]

        # 逐行解析
        for row_num, row in enumerate(reader, start=2):
            try:
                parsed_row = {}
                for orig_header, value in row.items():
                    orig_header = orig_header.strip()
                    if orig_header in header_map:
                        field = header_map[orig_header]
                        value = value.strip() if value else None
                        parsed_row[field] = _convert_field_value(field, value)

                # 检查必填字段值
                row_errors = []
                for field in required_fields:
                    if field not in parsed_row or parsed_row[field] is None or parsed_row[field] == "":
                        row_errors.append(f"第{row_num}行: 必填字段'{field_name_map.get(field, field)}'为空")

                if row_errors:
                    errors.extend(row_errors)
                    continue

                data_rows.append(parsed_row)

            except Exception as e:
                errors.append(f"第{row_num}行解析失败: {str(e)}")

    except Exception as e:
        errors.append(f"CSV解析错误: {str(e)}")

    return data_rows, errors


def _convert_field_value(field: str, value: Any) -> Any:
    """转换字段值到正确的类型"""
    if value is None or value == "":
        return None

    # 数值类型字段
    if field in ("student_count", "max_weekly_hours", "weekly_hours",
                 "total_hours", "credits", "priority", "capacity", "floor"):
        try:
            return int(value)
        except (ValueError, TypeError):
            return value

    # 布尔类型字段
    if field in ("requires_consecutive", "requires_lab", "has_multimedia", "is_available"):
        if isinstance(value, str):
            return value.lower() in ("yes", "true", "是", "1", "y")
        return bool(value)

    return value


def generate_csv_template(entity_type: str) -> str:
    """生成CSV导入模板

    Args:
        entity_type: 实体类型

    Returns:
        CSV模板内容（字符串，含表头）
    """
    if entity_type not in CSV_TEMPLATES:
        return ""

    template = CSV_TEMPLATES[entity_type]
    field_names = template["field_names"]
    all_fields = template["required_fields"] + template["optional_fields"]

    output = io.StringIO()
    writer = csv.writer(output)

    # 写入中文表头
    headers = [field_names.get(f, f) for f in all_fields]
    writer.writerow(headers)

    # 写入示例数据行
    examples = _get_example_data(entity_type)
    example_row = [examples.get(f, "") for f in all_fields]
    writer.writerow(example_row)

    return output.getvalue()


def _get_example_data(entity_type: str) -> Dict[str, Any]:
    """获取示例数据"""
    examples = {
        "classes": {
            "name": "计科1班", "grade": "大一", "student_count": "50",
            "department": "计算机科学", "homeroom_teacher": "张老师", "remarks": "示范数据"
        },
        "teachers": {
            "name": "李明", "teacher_code": "T001", "department": "计算机学院",
            "title": "教授", "email": "liming@university.edu.cn",
            "phone": "13800001001", "max_weekly_hours": "16", "remarks": "示范数据"
        },
        "courses": {
            "name": "数据结构", "course_code": "CS201", "course_type": "必修",
            "weekly_hours": "4", "total_hours": "64", "credits": "4",
            "requires_consecutive": "否", "requires_lab": "否",
            "priority": "5", "department": "计算机科学", "remarks": "示范数据"
        },
        "classrooms": {
            "name": "教学楼A-101", "room_code": "A101", "building": "教学楼A",
            "floor": "1", "capacity": "60", "room_type": "普通教室",
            "has_multimedia": "是", "remarks": "示范数据"
        },
        "syllabus": {
            "class_name": "计科1班", "class_grade": "大一", "student_count": "50",
            "department": "计算机科学",
            "course_name": "数据结构", "course_code": "CS201", "course_type": "必修",
            "weekly_hours": "4", "total_hours": "64", "credits": "4",
            "requires_consecutive": "否", "requires_lab": "否", "priority": "5",
        }
    }
    return examples.get(entity_type, {})
