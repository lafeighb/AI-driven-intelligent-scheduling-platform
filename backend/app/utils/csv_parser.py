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
    # 课程大纲模板 — 每行一个班级 + 动态多列课程（可自由扩展课程列数）
    "syllabus": {
        "required_fields": ["class_name", "class_grade"],  # 仅班级固定字段为必填
        "optional_fields": [],  # 课程列为动态生成，不走固定字段逻辑
        "field_names": {
            "class_name": "班级名称",
            "class_grade": "年级",
            "student_count": "学生人数",
            "department": "所属专业",
        },
        # 课程列模板 — 每个课程占用5列：名称、编码、类型、每周课时、总课时
        "course_column_count": 5,
        "course_columns": ["名称", "编码", "类型", "每周课时", "总课时"],
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

    # 大纲模板使用动态列生成
    if entity_type == "syllabus":
        return generate_syllabus_template()

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
        }
    }
    return examples.get(entity_type, {})


def generate_syllabus_template(course_count: int = 5) -> str:
    """生成课程大纲CSV模板（动态课程列数）

    格式：班级固定列 + 课程1~N 的5列组（名称、编码、类型、每周课时、总课时）
    用户可自由增减课程列数，导入时自动识别。
    """
    syllabus = CSV_TEMPLATES.get("syllabus", {})
    class_fields = ["class_name", "class_grade", "student_count", "department"]
    field_names = syllabus.get("field_names", {})
    course_cols = syllabus.get("course_columns", ["课程名称", "课程编码", "课程类型", "每周课时", "总课时"])

    output = io.StringIO()
    writer = csv.writer(output)

    # 表头：班级列 + 每门课程5列
    headers = [field_names.get(f, f) for f in class_fields]
    for i in range(1, course_count + 1):
        headers.extend([f"课程{i}{c}" for c in course_cols])
    writer.writerow(headers)

    # 示例数据：计科1班 + 3门课示例
    example = _get_example_data("syllabus")
    example_row = [example.get(f, "") for f in class_fields]
    # 示例课程
    demo_courses = [
        ["数据结构", "CS201", "必修", "4", "64"],
        ["操作系统", "CS301", "必修", "4", "64"],
        ["计算机网络", "CS302", "必修", "3", "48"],
    ]
    for c in demo_courses:
        example_row.extend(c)
    # 剩余课程列留空
    for _ in range(len(demo_courses), course_count):
        example_row.extend([""] * len(course_cols))
    writer.writerow(example_row)

    return output.getvalue()


def parse_syllabus_csv(content: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """解析课程大纲CSV（支持动态课程列数）

    自动检测表头中「课程N名称」模式的列，按N分组。
    返回每行展开为多条 {class_info + course_info} 的记录。
    """
    import re

    errors = []
    all_rows = []

    try:
        reader = csv.DictReader(io.StringIO(content))
        if reader.fieldnames is None:
            return [], ["CSV文件为空或格式错误"]

        headers = [h.strip() for h in reader.fieldnames]

        # 识别班级固定列
        class_col_map = {
            "班级名称": "class_name",
            "年级": "class_grade",
            "学生人数": "student_count",
            "所属专业": "department",
        }

        # 识别课程列组：匹配「课程N列名」模式
        course_groups: Dict[int, Dict[str, int]] = {}  # {课程序号: {列名: 列索引}}
        course_col_names = ["名称", "编码", "类型", "每周课时", "总课时"]

        # 列名到英文字段的映射（用于解析后的数据）
        course_field_map = {
            "名称": "course_name",
            "编码": "course_code",
            "类型": "course_type",
            "每周课时": "weekly_hours",
            "总课时": "total_hours",
        }

        for idx, h in enumerate(headers):
            # 匹配「课程1名称」、「课程2编码」等
            m = re.match(r"课程(\d+)(.+)", h)
            if m:
                group_num = int(m.group(1))
                col_name = m.group(2)
                if group_num not in course_groups:
                    course_groups[group_num] = {}
                course_groups[group_num][col_name] = idx

        if not course_groups:
            return [], ["未检测到课程列，请使用「课程1名称」「课程1编码」...格式添加课程列"]

        # 按序号排序
        sorted_groups = sorted(course_groups.items())

        for row_num, row in enumerate(reader, start=2):
            try:
                # 提取班级信息
                class_info = {}
                for cn_header, eng_field in class_col_map.items():
                    if cn_header in headers:
                        val = (row.get(cn_header) or "").strip()
                        if val:
                            # 类型转换
                            if eng_field == "student_count":
                                val = int(val) if val.isdigit() else None
                            class_info[eng_field] = val
                        else:
                            class_info[eng_field] = None

                if not class_info.get("class_name") or not class_info.get("class_grade"):
                    errors.append(f"第{row_num}行: 班级名称和年级为必填")
                    continue

                # 提取每个课程组
                has_course = False
                for group_num, col_map in sorted_groups:
                    course_info = {}
                    for cn_name, idx in col_map.items():
                        val = (row.get(headers[idx]) or "").strip()
                        course_info[cn_name] = val

                    course_name = course_info.get("名称", "")
                    course_code = course_info.get("编码", "")
                    if not course_name or not course_code:
                        continue  # 跳过空课程列

                    weekly_hours = course_info.get("每周课时", "")
                    weekly_hours = int(weekly_hours) if weekly_hours and weekly_hours.isdigit() else 2

                    total_hours = course_info.get("总课时", "")
                    total_hours = int(total_hours) if total_hours and total_hours.isdigit() else None

                    course_type = course_info.get("类型", "") or "必修"

                    # 合并班级信息 + 课程信息
                    combined = dict(class_info)
                    combined.update({
                        "course_name": course_name,
                        "course_code": course_code,
                        "course_type": course_type,
                        "weekly_hours": weekly_hours,
                        "total_hours": total_hours,
                    })
                    all_rows.append(combined)
                    has_course = True

                if not has_course:
                    errors.append(f"第{row_num}行: 未填写任何课程信息")

            except Exception as e:
                errors.append(f"第{row_num}行解析失败: {str(e)}")

    except Exception as e:
        errors.append(f"CSV解析错误: {str(e)}")

    return all_rows, errors
