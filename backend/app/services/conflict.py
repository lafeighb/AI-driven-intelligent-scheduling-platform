"""智能冲突检测与自动化解服务

支持多层冲突检测:
- 硬性冲突: 教师/教室/班级时间冲突、容量超限
- 软性冲突: 课时分布不均、连排要求未满足、教师偏好偏离
"""
from typing import List, Dict, Any, Set, Tuple, Optional
from collections import defaultdict
import json


class ConflictDetector:
    """多层冲突检测器"""

    def __init__(self, schedule_entries: List[Dict[str, Any]]):
        """初始化冲突检测器

        Args:
            schedule_entries: 排课条目列表
        """
        self.entries = schedule_entries
        self.hard_conflicts: List[Dict[str, Any]] = []
        self.soft_conflicts: List[Dict[str, Any]] = []
        self.conflict_stats: Dict[str, Any] = {}

    def detect_all(self) -> Tuple[List[Dict], List[Dict], Dict]:
        """执行全部冲突检测

        Returns:
            (hard_conflicts, soft_conflicts, stats)
        """
        self.hard_conflicts = []
        self.soft_conflicts = []

        self._detect_teacher_conflicts()
        self._detect_classroom_conflicts()
        self._detect_class_conflicts()
        self._detect_capacity_conflicts()
        self._detect_time_distribution_conflicts()
        self._detect_consecutive_requirement_conflicts()
        self._detect_teacher_preference_conflicts()
        self._compute_stats()

        return self.hard_conflicts, self.soft_conflicts, self.conflict_stats

    def _detect_teacher_conflicts(self):
        """检测教师时间冲突 - 同一教师同一时间被安排多门课程"""
        slot_map: Dict[Tuple[int, int, int, int], List[int]] = defaultdict(list)

        for entry in self.entries:
            teacher_id = entry.get("teacher_id")
            week = entry.get("week_number", 1)
            day = entry.get("day_of_week")
            period_start = entry.get("period_start")
            period_end = entry.get("period_end", period_start)

            for period in range(period_start, period_end + 1):
                key = (teacher_id, week, day, period)
                slot_map[key].append(entry.get("id", 0))

        for (teacher_id, week, day, period), entry_ids in slot_map.items():
            if len(entry_ids) > 1:
                self.hard_conflicts.append({
                    "conflict_type": "hard",
                    "category": "teacher",
                    "description": f"教师(ID:{teacher_id})在第{week}周 周{day} 第{period}节被安排了{len(entry_ids)}门课程",
                    "severity": 10.0,
                    "entries_involved": entry_ids,
                    "resolution_suggestion": f"将冲突的课程之一调整到其他时间段，或指定其他教师授课"
                })

    def _detect_classroom_conflicts(self):
        """检测教室占用冲突"""
        slot_map: Dict[Tuple[int, int, int, int], List[int]] = defaultdict(list)

        for entry in self.entries:
            classroom_id = entry.get("classroom_id")
            week = entry.get("week_number", 1)
            day = entry.get("day_of_week")
            period_start = entry.get("period_start")
            period_end = entry.get("period_end", period_start)

            for period in range(period_start, period_end + 1):
                key = (classroom_id, week, day, period)
                slot_map[key].append(entry.get("id", 0))

        for (classroom_id, week, day, period), entry_ids in slot_map.items():
            if len(entry_ids) > 1:
                self.hard_conflicts.append({
                    "conflict_type": "hard",
                    "category": "classroom",
                    "description": f"教室(ID:{classroom_id})在第{week}周 周{day} 第{period}节被重复占用",
                    "severity": 10.0,
                    "entries_involved": entry_ids,
                    "resolution_suggestion": f"将冲突课程调整到空闲教室或不同时间段"
                })

    def _detect_class_conflicts(self):
        """检测班级课程冲突 - 同一班级同一时间不能上多门课"""
        slot_map: Dict[Tuple[int, int, int, int], List[int]] = defaultdict(list)

        for entry in self.entries:
            class_id = entry.get("class_id")
            week = entry.get("week_number", 1)
            day = entry.get("day_of_week")
            period_start = entry.get("period_start")
            period_end = entry.get("period_end", period_start)

            for period in range(period_start, period_end + 1):
                key = (class_id, week, day, period)
                slot_map[key].append(entry.get("id", 0))

        for (class_id, week, day, period), entry_ids in slot_map.items():
            if len(entry_ids) > 1:
                self.hard_conflicts.append({
                    "conflict_type": "hard",
                    "category": "class",
                    "description": f"班级(ID:{class_id})在第{week}周 周{day} 第{period}节被安排了{len(entry_ids)}门课程",
                    "severity": 10.0,
                    "entries_involved": entry_ids,
                    "resolution_suggestion": f"将冲突课程调整到该班级的其他空闲时间"
                })

    def _detect_capacity_conflicts(self):
        """检测教室容量冲突"""
        for entry in self.entries:
            class_count = entry.get("student_count", 0)
            room_capacity = entry.get("room_capacity", 0)

            if class_count > 0 and room_capacity > 0:
                if class_count > room_capacity:
                    self.hard_conflicts.append({
                        "conflict_type": "hard",
                        "category": "capacity",
                        "description": (f"教室容量不足: 学生{entry.get('class_name', '')}"
                                       f"有{class_count}人，但教室{entry.get('classroom_name', '')}"
                                       f"仅能容纳{room_capacity}人"),
                        "severity": 8.0,
                        "entries_involved": [entry.get("id", 0)],
                        "resolution_suggestion": "更换到更大的教室或调整班级分配"
                    })
                elif class_count < room_capacity * 0.3:
                    self.soft_conflicts.append({
                        "conflict_type": "soft",
                        "category": "capacity",
                        "description": (f"教室利用率低: {entry.get('class_name', '')}({class_count}人)"
                                       f"使用{entry.get('classroom_name', '')}({room_capacity}座)"),
                        "severity": 2.0,
                        "entries_involved": [entry.get("id", 0)],
                        "resolution_suggestion": "考虑更换更小的教室以优化资源利用"
                    })

    def _detect_time_distribution_conflicts(self):
        """检测课程时间分布合理性问题"""
        # 按课程统计每天课时
        course_day_count: Dict[Tuple[int, int], int] = defaultdict(int)
        course_day_entries: Dict[Tuple[int, int], List[int]] = defaultdict(list)

        for entry in self.entries:
            course_id = entry.get("course_id")
            day = entry.get("day_of_week")
            hours = (entry.get("period_end", entry.get("period_start"))
                    - entry.get("period_start", 1) + 1)
            course_day_count[(course_id, day)] += hours
            course_day_entries[(course_id, day)].append(entry.get("id", 0))

        # 检测同一天同一课程过于集中
        for (course_id, day), total_hours in course_day_count.items():
            if total_hours > 3:
                self.soft_conflicts.append({
                    "conflict_type": "soft",
                    "category": "time",
                    "description": (f"课程(ID:{course_id}) 在周{day}共有{total_hours}课时，"
                                   f"分布可能过于集中，建议分散安排"),
                    "severity": 4.0,
                    "entries_involved": course_day_entries[(course_id, day)],
                    "resolution_suggestion": "将该课程的部分课时调整到其他天"
                })

        # 检测班级每天课时均衡性
        class_day_hours: Dict[Tuple[int, int], int] = defaultdict(int)
        for entry in self.entries:
            class_id = entry.get("class_id")
            day = entry.get("day_of_week")
            hours = (entry.get("period_end", entry.get("period_start"))
                    - entry.get("period_start", 1) + 1)
            class_day_hours[(class_id, day)] += hours

        # 按班级检查
        class_ids = set(e.get("class_id") for e in self.entries)
        for class_id in class_ids:
            day_hours = {d: class_day_hours.get((class_id, d), 0) for d in range(1, 6)}
            if day_hours:
                max_h = max(day_hours.values())
                min_h = min(day_hours.values())
                if max_h - min_h > 4:
                    self.soft_conflicts.append({
                        "conflict_type": "soft",
                        "category": "time",
                        "description": (f"班级(ID:{class_id})每日课时分布不均: "
                                       f"最多{max_h}课时, 最少{min_h}课时，差距达{max_h - min_h}课时"),
                        "severity": 5.0,
                        "entries_involved": [],
                        "resolution_suggestion": "重新分配课程时间，使每日课时更均衡"
                    })

    def _detect_consecutive_requirement_conflicts(self):
        """检测连排要求是否满足"""
        # 找出所有需要连排的课程
        for entry in self.entries:
            if entry.get("requires_consecutive"):
                period_start = entry.get("period_start", 1)
                period_end = entry.get("period_end", period_start)
                if period_end - period_start < 1:
                    self.soft_conflicts.append({
                        "conflict_type": "soft",
                        "category": "course",
                        "description": (f"课程'{entry.get('course_name', '')}'要求连排(连续2节)，"
                                       f"但当前仅安排了1节"),
                        "severity": 6.0,
                        "entries_involved": [entry.get("id", 0)],
                        "resolution_suggestion": "将该课程调整到连续的两节课时间"
                    })

    def _detect_teacher_preference_conflicts(self):
        """检测教师偏好满足情况"""
        for entry in self.entries:
            preferred = entry.get("preferred_time_slots")
            if preferred:
                try:
                    pref = json.loads(preferred) if isinstance(preferred, str) else preferred
                    day = entry.get("day_of_week")
                    period = entry.get("period_start")
                    slot_key = f"{day}-{period}"
                    if slot_key not in pref:
                        self.soft_conflicts.append({
                            "conflict_type": "soft",
                            "category": "teacher",
                            "description": (f"教师'{entry.get('teacher_name', '')}'的课程安排在"
                                           f"周{day}第{period}节，非其偏好时间"),
                            "severity": 3.0,
                            "entries_involved": [entry.get("id", 0)],
                            "resolution_suggestion": "如有可能，调整到教师偏好的时间段"
                        })
                except (json.JSONDecodeError, TypeError):
                    pass

    def _compute_stats(self):
        """计算冲突统计信息"""
        self.conflict_stats = {
            "total_hard_conflicts": len(self.hard_conflicts),
            "total_soft_conflicts": len(self.soft_conflicts),
            "conflict_free": len(self.hard_conflicts) == 0,
            "hard_by_category": self._count_by_category(self.hard_conflicts),
            "soft_by_category": self._count_by_category(self.soft_conflicts),
            "avg_hard_severity": (sum(c["severity"] for c in self.hard_conflicts)
                                 / max(1, len(self.hard_conflicts))),
            "avg_soft_severity": (sum(c["severity"] for c in self.soft_conflicts)
                                 / max(1, len(self.soft_conflicts))),
            "total_entries": len(self.entries),
            "entries_in_conflict": len(set(
                eid for c in self.hard_conflicts + self.soft_conflicts
                for eid in c.get("entries_involved", [])
            )),
        }

    @staticmethod
    def _count_by_category(conflicts: List[Dict]) -> Dict[str, int]:
        """按类别统计冲突数"""
        counts: Dict[str, int] = defaultdict(int)
        for c in conflicts:
            counts[c.get("category", "unknown")] += 1
        return dict(counts)

    def get_resolution_plan(self) -> List[Dict[str, Any]]:
        """生成冲突化解方案"""
        plan = []

        # 按严重程度排序
        all_conflicts = sorted(
            self.hard_conflicts + self.soft_conflicts,
            key=lambda c: c["severity"], reverse=True
        )

        for conflict in all_conflicts:
            if conflict["conflict_type"] == "hard":
                action = "immediate"  # 硬冲突必须立即处理
            else:
                action = "suggested"  # 软冲突建议处理

            plan.append({
                "conflict_description": conflict["description"],
                "action_type": action,
                "severity": conflict["severity"],
                "suggestion": conflict.get("resolution_suggestion", ""),
                "entries_involved": conflict.get("entries_involved", []),
            })

        return plan
