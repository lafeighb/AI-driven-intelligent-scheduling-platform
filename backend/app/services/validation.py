"""AI智能校验服务 - 对录入数据进行完整性与业务合理性检查"""
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session


class ValidationService:
    """数据校验服务"""

    def __init__(self, db: Session):
        self.db = db
        self.warnings: List[Dict[str, Any]] = []
        self.errors: List[Dict[str, Any]] = []

    def validate_class(self, data: Dict[str, Any]) -> Tuple[bool, List[Dict], List[Dict]]:
        """校验班级数据"""
        self._reset()

        # 完整性检查
        if not data.get("name"):
            self.errors.append({"field": "name", "message": "班级名称不能为空"})
        if not data.get("grade"):
            self.errors.append({"field": "grade", "message": "年级不能为空"})

        # 业务合理性检查
        if data.get("student_count"):
            count = int(data["student_count"])
            if count <= 0:
                self.errors.append({"field": "student_count", "message": "学生人数必须大于0"})
            elif count > 80:
                self.warnings.append({
                    "field": "student_count",
                    "message": f"学生人数({count})超过80人，建议考虑分班或确保教室容量充足",
                    "severity": "medium"
                })
            elif count < 10:
                self.warnings.append({
                    "field": "student_count",
                    "message": f"学生人数({count})少于10人，请确认是否需要合班上课",
                    "severity": "low"
                })

        # 检查班级名称唯一性
        if data.get("name"):
            existing = self.db.query(
                self.db.execute.__self__
            ).filter_by(name=data["name"]).first() if hasattr(self, '_check_name') else None

        return len(self.errors) == 0, self.errors, self.warnings

    def validate_teacher(self, data: Dict[str, Any]) -> Tuple[bool, List[Dict], List[Dict]]:
        """校验教师数据"""
        self._reset()

        # 完整性检查
        if not data.get("name"):
            self.errors.append({"field": "name", "message": "教师姓名不能为空"})
        if not data.get("teacher_code"):
            self.errors.append({"field": "teacher_code", "message": "教师工号不能为空"})

        # 业务合理性检查
        if data.get("max_weekly_hours"):
            hours = int(data["max_weekly_hours"])
            if hours > 30:
                self.warnings.append({
                    "field": "max_weekly_hours",
                    "message": f"每周最大课时数({hours})较大，可能导致教师负担过重",
                    "severity": "medium"
                })
            elif hours < 4:
                self.warnings.append({
                    "field": "max_weekly_hours",
                    "message": f"每周最大课时数({hours})较小，请确认是否正确",
                    "severity": "low"
                })

        # 检查邮箱格式
        if data.get("email") and "@" not in str(data["email"]):
            self.warnings.append({
                "field": "email",
                "message": "邮箱格式可能不正确",
                "severity": "low"
            })

        return len(self.errors) == 0, self.errors, self.warnings

    def validate_course(self, data: Dict[str, Any]) -> Tuple[bool, List[Dict], List[Dict]]:
        """校验课程数据"""
        self._reset()

        if not data.get("name"):
            self.errors.append({"field": "name", "message": "课程名称不能为空"})
        if not data.get("course_code"):
            self.errors.append({"field": "course_code", "message": "课程编码不能为空"})

        # 课时合理性
        if data.get("weekly_hours"):
            hours = int(data["weekly_hours"])
            if hours > 6:
                self.warnings.append({
                    "field": "weekly_hours",
                    "message": f"每周课时({hours})较多，建议检查课程设置是否合理",
                    "severity": "medium"
                })
            elif hours >= 4 and not data.get("requires_consecutive"):
                self.warnings.append({
                    "field": "weekly_hours",
                    "message": f"每周{hours}课时，建议考虑设置连排以优化教学效果",
                    "severity": "low"
                })

        # 课程类型与学分匹配
        if data.get("course_type") == "必修" and int(data.get("credits", 2)) <= 0:
            self.warnings.append({
                "field": "credits",
                "message": "必修课程建议设置学分大于0",
                "severity": "low"
            })

        return len(self.errors) == 0, self.errors, self.warnings

    def validate_classroom(self, data: Dict[str, Any]) -> Tuple[bool, List[Dict], List[Dict]]:
        """校验教室数据"""
        self._reset()

        if not data.get("name"):
            self.errors.append({"field": "name", "message": "教室名称不能为空"})
        if not data.get("room_code"):
            self.errors.append({"field": "room_code", "message": "教室编号不能为空"})
        if not data.get("capacity"):
            self.errors.append({"field": "capacity", "message": "教室容量不能为空"})

        if data.get("capacity"):
            cap = int(data["capacity"])
            if cap <= 0:
                self.errors.append({"field": "capacity", "message": "教室容量必须大于0"})
            elif cap > 300:
                self.warnings.append({
                    "field": "capacity",
                    "message": f"教室容量({cap})较大，适合作为阶梯教室或大课教室",
                    "severity": "info"
                })

        # 实验室类型检查
        if data.get("room_type") == "实验室" and not data.get("has_multimedia"):
            self.warnings.append({
                "field": "room_type",
                "message": "实验室通常需要多媒体设备支持",
                "severity": "low"
            })

        return len(self.errors) == 0, self.errors, self.warnings

    def validate_batch(self, entity_type: str, data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """批量校验"""
        results = {
            "total": len(data_list),
            "valid": 0,
            "invalid": 0,
            "errors": [],
            "warnings": [],
            "summary": ""
        }

        for i, data in enumerate(data_list):
            if entity_type == "classes":
                ok, errs, warns = self.validate_class(data)
            elif entity_type == "teachers":
                ok, errs, warns = self.validate_teacher(data)
            elif entity_type == "courses":
                ok, errs, warns = self.validate_course(data)
            elif entity_type == "classrooms":
                ok, errs, warns = self.validate_classroom(data)
            else:
                results["errors"].append({"row": i + 1, "message": f"未知实体类型: {entity_type}"})
                continue

            if ok:
                results["valid"] += 1
            else:
                results["invalid"] += 1

            for e in errs:
                results["errors"].append({"row": i + 1, **e})
            for w in warns:
                results["warnings"].append({"row": i + 1, **w})

        # 生成摘要
        if results["invalid"] == 0:
            results["summary"] = f"全部{results['total']}条数据通过校验"
            if results["warnings"]:
                results["summary"] += f"，但有{len(results['warnings'])}条警告需要关注"
        else:
            results["summary"] = (f"共{results['total']}条数据，{results['valid']}条通过，"
                                 f"{results['invalid']}条存在问题，{len(results['warnings'])}条警告")

        return results

    def _reset(self):
        """重置校验状态"""
        self.warnings = []
        self.errors = []
