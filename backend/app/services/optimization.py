"""排课约束自学习与动态优化服务

基于历史排课数据，通过统计分析和机器学习方法：
1. 分析各约束在历史方案中的被满足频率
2. 评估约束冲突的严重程度
3. 量化约束对最终方案质量的影响
4. 动态调整约束权重以优化未来排课
"""
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import json
from datetime import datetime


class ConstraintLearningService:
    """约束自学习服务"""

    def __init__(self):
        self.history_data: List[Dict] = []
        self.analysis_results: Dict[str, Any] = {}

    def load_history(self, history_data: List[Dict]):
        """加载历史排课数据

        Args:
            history_data: 历史排课记录，每条包含约束条件、排课方案、质量评估
        """
        self.history_data = history_data

    def analyze_constraint_satisfaction(self, constraints: List[Dict],
                                        schedule_data: List[Dict]) -> List[Dict]:
        """分析各约束的满足情况

        Args:
            constraints: 约束规则列表
            schedule_data: 排课方案数据

        Returns:
            各约束的满足率分析结果
        """
        results = []
        total_entries = max(1, len(schedule_data))

        for constraint in constraints:
            rule_type = constraint.get("rule_type", "soft")
            category = constraint.get("category", "")
            rule_expr = constraint.get("rule_expression", "{}")

            try:
                expr = json.loads(rule_expr) if isinstance(rule_expr, str) else rule_expr
            except (json.JSONDecodeError, TypeError):
                expr = {}

            # 统计该约束在方案中的违反次数
            violation_count = self._count_violations(constraint, schedule_data)

            # 计算满足率
            satisfaction_rate = 1.0 - (violation_count / total_entries)
            satisfaction_rate = max(0.0, min(1.0, satisfaction_rate))

            # 计算冲突严重程度(0-10)
            severity = min(10.0, violation_count * constraint.get("penalty_score", 1.0) / total_entries * 10)

            results.append({
                "rule_id": constraint.get("id"),
                "rule_name": constraint.get("name", "未命名规则"),
                "rule_type": rule_type,
                "category": category,
                "satisfaction_rate": round(satisfaction_rate, 4),
                "violation_count": violation_count,
                "conflict_severity_mean": round(severity, 2),
                "is_active": constraint.get("is_active", True),
            })

        return results

    def learn_from_history(self, historical_schedules: List[Dict],
                          historical_constraints: List[Dict]) -> Dict[str, Any]:
        """从历史数据中学习约束权重和模式

        Args:
            historical_schedules: 历史排课方案列表
            historical_constraints: 历史上使用的约束

        Returns:
            学习结果，包含推荐的约束调整
        """
        if not historical_schedules:
            return {"message": "历史数据不足，无法进行有效学习"}

        # 1. 统计各约束的历史满足率
        constraint_stats = defaultdict(lambda: {
            "violations": [], "satisfaction_rates": [], "quality_scores": []
        })

        for schedule_record in historical_schedules:
            quality = schedule_record.get("quality_score", 50)
            constraints_used = schedule_record.get("constraints", [])
            violations = schedule_record.get("violations", {})

            for c in constraints_used:
                c_id = c.get("id") or c.get("name")
                v_count = violations.get(str(c_id), 0)
                constraint_stats[c_id]["violations"].append(v_count)
                constraint_stats[c_id]["quality_scores"].append(quality)

        # 2. 分析每个约束的影响
        constraint_impacts = []
        for c_id, stats in constraint_stats.items():
            violations_arr = np.array(stats["violations"])
            quality_arr = np.array(stats["quality_scores"])

            avg_violations = float(np.mean(violations_arr)) if len(violations_arr) > 0 else 0
            avg_quality = float(np.mean(quality_arr)) if len(quality_arr) > 0 else 0

            # 计算违反次数与方案质量的相关性
            correlation = 0.0
            if len(violations_arr) > 2 and len(quality_arr) > 2:
                try:
                    corr_matrix = np.corrcoef(violations_arr, quality_arr)
                    correlation = float(corr_matrix[0, 1]) if not np.isnan(corr_matrix[0, 1]) else 0.0
                except Exception:
                    correlation = 0.0

            # 生成推荐
            if avg_violations > 5:
                recommendation = f"该约束平均违反{avg_violations:.1f}次，建议降低权重或调整为软约束"
                suggested_weight = max(0.5, 5.0 - avg_violations * 0.5)
            elif correlation < -0.3:
                recommendation = f"该约束与方案质量呈负相关(r={correlation:.2f})，建议保留并适当提高权重"
                suggested_weight = min(10.0, 5.0 + abs(correlation) * 10)
            else:
                recommendation = "该约束表现正常，建议维持当前设置"
                suggested_weight = 5.0

            constraint_impacts.append({
                "rule_id": c_id,
                "avg_violations": round(avg_violations, 2),
                "impact_on_quality": round(correlation, 3),
                "avg_quality_when_active": round(avg_quality, 1),
                "recommendation": recommendation,
                "suggested_weight": round(suggested_weight, 1),
            })

        # 3. 全局分析
        constraint_impacts.sort(key=lambda x: abs(x["impact_on_quality"]), reverse=True)

        # 计算理想权重分配
        total_impact = sum(abs(c["impact_on_quality"]) for c in constraint_impacts) or 1
        for c in constraint_impacts:
            c["normalized_importance"] = round(abs(c["impact_on_quality"]) / total_impact, 4)

        self.analysis_results = {
            "analysis_time": datetime.now().isoformat(),
            "total_historical_records": len(historical_schedules),
            "constraint_impacts": constraint_impacts,
            "summary": self._generate_learning_summary(constraint_impacts),
        }

        return self.analysis_results

    def recommend_constraint_adjustments(self, current_constraints: List[Dict],
                                        learning_results: Dict) -> List[Dict]:
        """根据学习结果推荐约束调整

        Args:
            current_constraints: 当前约束配置
            learning_results: 学习分析结果

        Returns:
            推荐的约束调整列表
        """
        recommendations = []
        impacts = {c["rule_id"]: c for c in learning_results.get("constraint_impacts", [])}

        for constraint in current_constraints:
            c_id = constraint.get("id") or constraint.get("name")
            impact = impacts.get(str(c_id))

            if impact:
                adjustment = {
                    "rule_id": constraint.get("id"),
                    "rule_name": constraint.get("name"),
                    "current_weight": constraint.get("weight", 5.0),
                    "suggested_weight": impact.get("suggested_weight", 5.0),
                    "current_type": constraint.get("rule_type"),
                    "suggested_type": constraint.get("rule_type"),
                    "reason": impact.get("recommendation", ""),
                    "confidence": round(abs(impact.get("impact_on_quality", 0)), 2),
                }

                # 如果违反频繁且为软约束，建议降低权重
                if impact.get("avg_violations", 0) > 8 and constraint.get("rule_type") == "hard":
                    adjustment["suggested_type"] = "soft"
                    adjustment["reason"] += "。由于频繁违反，建议将此硬约束降级为软约束"

                recommendations.append(adjustment)

        return recommendations

    def generate_historical_dataset(self) -> List[Dict]:
        """生成用于学习的示例历史数据集

        Returns:
            模拟历史排课数据集
        """
        # 生成一个包含约束条件和最终排课方案的小型数据集
        dataset = []

        # 模拟数据模式
        base_scenarios = [
            {"name": "上学期排课v1", "quality": 85, "hard_violations": 2, "soft_violations": 15},
            {"name": "上学期排课v2", "quality": 78, "hard_violations": 5, "soft_violations": 20},
            {"name": "上学期排课v3", "quality": 92, "hard_violations": 0, "soft_violations": 8},
            {"name": "调整方案v1", "quality": 88, "hard_violations": 1, "soft_violations": 12},
            {"name": "调整方案v2", "quality": 95, "hard_violations": 0, "soft_violations": 5},
        ]

        for i, scenario in enumerate(base_scenarios):
            record = {
                "id": i + 1,
                "version": scenario["name"],
                "timestamp": f"2025-0{9-i}-01T10:00:00",
                "quality_score": scenario["quality"],
                "total_entries": 200 + i * 10,
                "hard_violations": scenario["hard_violations"],
                "soft_violations": scenario["soft_violations"],
                "constraints": [
                    {"id": "1", "name": "教师时间不冲突", "type": "hard"},
                    {"id": "2", "name": "教室不重复占用", "type": "hard"},
                    {"id": "3", "name": "班级课程不冲突", "type": "hard"},
                    {"id": "4", "name": "教师时间偏好", "type": "soft"},
                    {"id": "5", "name": "课时均匀分布", "type": "soft"},
                    {"id": "6", "name": "连排课程要求", "type": "soft"},
                    {"id": "7", "name": "教室容量匹配", "type": "soft"},
                ],
                "violations": {
                    "1": max(0, scenario["hard_violations"] // 2),
                    "2": max(0, scenario["hard_violations"] // 2),
                    "3": 0,
                    "4": max(0, scenario["soft_violations"] // 2),
                    "5": max(0, scenario["soft_violations"] // 3),
                    "6": max(0, scenario["soft_violations"] // 4),
                    "7": max(0, scenario["soft_violations"] // 6),
                },
                "constraint_satisfaction_rates": {
                    "1": 1.0 - scenario["hard_violations"] / 400,
                    "2": 1.0 - scenario["hard_violations"] / 400,
                    "3": 1.0,
                    "4": 1.0 - scenario["soft_violations"] / 400,
                    "5": 1.0 - scenario["soft_violations"] / 300,
                    "6": 1.0 - scenario["soft_violations"] / 200,
                    "7": 1.0 - scenario["soft_violations"] / 250,
                },
            }
            dataset.append(record)

        return dataset

    def _count_violations(self, constraint: Dict, schedule_data: List[Dict]) -> int:
        """统计特定约束在方案中的违反次数"""
        # 基于约束类型和分类进行启发式计数
        rule_type = constraint.get("rule_type", "")
        category = constraint.get("category", "")
        count = 0

        if category == "teacher":
            count = self._count_teacher_violations(schedule_data)
        elif category == "classroom":
            count = self._count_classroom_violations(schedule_data)
        elif category == "class":
            count = self._count_class_violations(schedule_data)
        elif category == "time":
            count = self._count_time_violations(schedule_data)
        elif category == "course":
            count = self._count_course_violations(schedule_data)

        return count

    def _count_teacher_violations(self, data: List[Dict]) -> int:
        count = 0
        slot_map = defaultdict(list)
        for entry in data:
            key = (entry.get("teacher_id"), entry.get("day_of_week"), entry.get("period_start"))
            slot_map[key].append(entry)
        for entries in slot_map.values():
            if len(entries) > 1:
                count += len(entries) - 1
        return count

    def _count_classroom_violations(self, data: List[Dict]) -> int:
        count = 0
        slot_map = defaultdict(list)
        for entry in data:
            key = (entry.get("classroom_id"), entry.get("day_of_week"), entry.get("period_start"))
            slot_map[key].append(entry)
        for entries in slot_map.values():
            if len(entries) > 1:
                count += len(entries) - 1
        return count

    def _count_class_violations(self, data: List[Dict]) -> int:
        count = 0
        slot_map = defaultdict(list)
        for entry in data:
            key = (entry.get("class_id"), entry.get("day_of_week"), entry.get("period_start"))
            slot_map[key].append(entry)
        for entries in slot_map.values():
            if len(entries) > 1:
                count += len(entries) - 1
        return count

    def _count_time_violations(self, data: List[Dict]) -> int:
        course_day = defaultdict(int)
        for entry in data:
            course_day[(entry.get("course_id"), entry.get("day_of_week"))] += 1
        return sum(max(0, c - 2) for c in course_day.values())

    def _count_course_violations(self, data: List[Dict]) -> int:
        return sum(1 for e in data
                  if e.get("requires_consecutive")
                  and (e.get("period_end", e.get("period_start"))
                      - e.get("period_start", 1) < 1))

    def _generate_learning_summary(self, impacts: List[Dict]) -> str:
        """生成学习分析摘要"""
        if not impacts:
            return "暂无足够数据进行约束学习分析。"

        high_impact = [c for c in impacts if abs(c.get("impact_on_quality", 0)) > 0.5]
        low_satisfaction = [c for c in impacts if c.get("avg_violations", 0) > 5]

        parts = []
        if high_impact:
            parts.append(f"发现{len(high_impact)}个约束对方案质量有显著影响")
        if low_satisfaction:
            parts.append(f"{len(low_satisfaction)}个约束的历史满足率偏低")

        if parts:
            return "；".join(parts) + "。建议根据分析结果调整约束权重和类型。"
        return "各约束表现稳定，无需重大调整。"
