"""AI排课方案解释生成服务

根据排课结果和约束满足情况，生成自然语言解释说明，
总结排课的决策逻辑与权衡结果。
"""
from typing import Dict, Any, List, Optional
import json


class ExplanationGenerator:
    """AI优化说明生成器"""

    def __init__(self):
        self.templates = {
            "constraint_satisfaction": {
                "full": "本次方案100%满足了所有{category}要求",
                "high": "本次方案{rate}%满足了{category}要求",
                "partial": "在{category}方面，满足了{rate}%的要求",
                "low": "{category}方面仅满足{rate}%，需进一步优化",
            },
            "tradeoff": {
                "balanced": "在{aspect1}和{aspect2}之间取得了较好的平衡",
                "prioritized": "本次方案优先{priority}；在此前提下，兼顾了{secondary}",
                "compromise": "由于{reason}，在{aspect}上做了适当妥协",
            },
            "improvement": {
                "up": "较上一版提升了{metric}{value}%",
                "down": "较上一版降低了{metric}{value}%",
                "stable": "与上一版相比，{metric}保持稳定",
            },
        }

    def generate(self, schedule_result: Dict[str, Any],
                 constraint_stats: Optional[Dict] = None,
                 conflicts: Optional[Dict] = None,
                 learning_data: Optional[Dict] = None,
                 previous_result: Optional[Dict] = None) -> str:
        """生成完整的AI优化说明

        Args:
            schedule_result: 排课结果
            constraint_stats: 约束满足统计
            conflicts: 冲突检测结果
            learning_data: 约束学习数据
            previous_result: 上一版排课结果（用于对比）

        Returns:
            自然语言格式的优化说明
        """
        parts = []

        # 1. 总体概述
        parts.append(self._generate_overview(schedule_result))

        # 2. 硬约束满足情况
        if conflicts:
            parts.append(self._generate_hard_constraint_summary(conflicts))

        # 3. 软约束满足情况
        if constraint_stats:
            parts.append(self._generate_soft_constraint_summary(constraint_stats))

        # 4. 优化目标达成情况
        parts.append(self._generate_optimization_summary(schedule_result))

        # 5. 与前版对比
        if previous_result:
            parts.append(self._generate_comparison(schedule_result, previous_result))

        # 6. 建议与展望
        parts.append(self._generate_suggestions(schedule_result, conflicts))

        return "\n\n".join(parts)

    def _generate_overview(self, result: Dict) -> str:
        """生成总体概述"""
        quality = result.get("quality_score", 0)
        total = result.get("total_entries", 0)
        hard = result.get("hard_conflicts", 0)
        soft = result.get("soft_conflicts", 0)

        level = "优秀" if quality >= 90 else "良好" if quality >= 75 else "一般" if quality >= 60 else "有待改善"

        overview = (f"【总体评价】本次排课方案质量评分为{quality}分（{level}等级），"
                   f"共生成{total}条排课记录。")

        if hard == 0:
            overview += "所有硬性约束均已完全满足，无教师/教室/班级时间冲突。"
        else:
            overview += f"存在{hard}个硬性冲突需要优先解决。"

        if soft == 0:
            overview += "软约束也得到完美满足。"
        elif soft <= 5:
            overview += f"仅有{soft}个轻微的软约束偏离。"
        else:
            overview += f"存在{soft}个软约束偏离，建议后续优化。"

        return overview

    def _generate_hard_constraint_summary(self, conflicts: Dict) -> str:
        """生成硬约束满足总结"""
        hard_conflicts = conflicts.get("hard_conflicts", [])
        stats = conflicts.get("conflict_stats", {})

        if not hard_conflicts:
            return ("【硬约束检查】✓ 全部通过。所有核心约束均已满足："
                   "无教师时间冲突、无教室重复占用、无班级课程重叠、"
                   "所有教室容量满足上课人数要求。")

        by_category = stats.get("hard_by_category", {})
        details = []
        for cat, count in by_category.items():
            cat_name = {"teacher": "教师时间冲突", "classroom": "教室占用冲突",
                       "class": "班级课程重叠", "capacity": "教室容量不足"}
            details.append(f"{cat_name.get(cat, cat)}{count}处")

        return f"【硬约束检查】✗ 发现{len(hard_conflicts)}个硬性冲突：{'、'.join(details)}。需要优先处理。"

    def _generate_soft_constraint_summary(self, constraint_stats: Dict) -> str:
        """生成软约束满足总结"""
        if not constraint_stats:
            return ""

        # 从学习数据或统计数据中提取软约束满足率
        impacts = constraint_stats.get("constraint_impacts", [])
        summary = constraint_stats.get("summary", "")

        lines = ["【软约束优化】"]
        satisfaction_details = []

        for impact in impacts[:5]:  # 取前5个最重要的
            rule_id = impact.get("rule_id", "")
            rate = impact.get("satisfaction_rate", impact.get("avg_violations", 0))
            rec = impact.get("recommendation", "")

            if isinstance(rate, float) and rate <= 1.0:
                pct = int(rate * 100)
                satisfaction_details.append(f"• {impact.get('rule_name', rule_id)}: 满足率约{pct}%")
            else:
                satisfaction_details.append(
                    f"• {impact.get('rule_name', rule_id)}: 平均偏离{rate}次")

        if satisfaction_details:
            lines.extend(satisfaction_details)
        else:
            lines.append("各项软约束均得到合理满足。")

        if summary:
            lines.append(f"\n分析摘要：{summary}")

        return "\n".join(lines)

    def _generate_optimization_summary(self, result: Dict) -> str:
        """生成优化目标达成总结"""
        quality = result.get("quality_score", 0)
        algorithm = result.get("algorithm", "遗传算法")

        lines = ["【优化策略】"]

        # 根据算法类型和结果生成不同的描述
        if quality >= 90:
            lines.append(f"通过{algorithm}的深度优化，本次排课方案达到了近乎最优的效果。")
            lines.append("系统在以下维度进行了综合权衡：")
            lines.append("• 首要目标：完全消除硬性冲突，确保教学秩序")
            lines.append("• 第二目标：最大化教师时间偏好满足率")
            lines.append("• 第三目标：优化教室资源利用率，降低闲置率")
            lines.append("• 辅助目标：均衡班级每日课时分布，提升学习体验")
        elif quality >= 75:
            lines.append(f"通过{algorithm}的有效搜索，本次排课方案达到了良好水平。")
            lines.append("系统优先保证了核心约束的满足，在软约束方面尚有一定优化空间。")
        else:
            lines.append(f"{algorithm}找到了可行解，但方案质量有提升空间。")
            lines.append("建议：增加约束权重调整的灵活性，或扩充教师/教室资源以降低排课难度。")

        # 添加具体的优化指标
        if result.get("execution_time"):
            lines.append(f"\n排课耗时：{result['execution_time']:.1f}秒")

        return "\n".join(lines)

    def _generate_comparison(self, current: Dict, previous: Dict) -> str:
        """生成与历史版本的对比"""
        curr_quality = current.get("quality_score", 0)
        prev_quality = previous.get("quality_score", 0)
        curr_hard = current.get("hard_conflicts", 0)
        prev_hard = previous.get("hard_conflicts", 0)
        curr_soft = current.get("soft_conflicts", 0)
        prev_soft = previous.get("soft_conflicts", 0)

        lines = ["【版本对比】"]

        quality_diff = curr_quality - prev_quality
        if quality_diff > 0:
            lines.append(f"• 方案质量提升{quality_diff:.1f}分（{prev_quality} → {curr_quality}）")
        elif quality_diff < 0:
            lines.append(f"• 方案质量下降{abs(quality_diff):.1f}分（{prev_quality} → {curr_quality}）")
        else:
            lines.append("• 方案质量与上版持平")

        hard_diff = curr_hard - prev_hard
        if hard_diff < 0:
            lines.append(f"• 硬性冲突减少{abs(hard_diff)}个（{prev_hard} → {curr_hard}）")
        elif hard_diff > 0:
            lines.append(f"• 硬性冲突增加{hard_diff}个（{prev_hard} → {curr_hard}）")

        soft_diff = curr_soft - prev_soft
        if soft_diff < 0:
            lines.append(f"• 软性冲突减少{abs(soft_diff)}个（{prev_soft} → {curr_soft}）")
        elif soft_diff > 0:
            lines.append(f"• 软性冲突增加{soft_diff}个（{prev_soft} → {curr_soft}）")

        return "\n".join(lines)

    def _generate_suggestions(self, result: Dict, conflicts: Optional[Dict]) -> str:
        """生成改进建议"""
        quality = result.get("quality_score", 0)
        hard_count = result.get("hard_conflicts", 0)

        lines = ["【改进建议】"]

        if hard_count > 0:
            lines.append("1. 优先解决硬性冲突：检查教师和教室的可用时间，确保无重复分配。")
            lines.append("2. 考虑增加教师资源或调整部分课程的开课时间。")

        if quality < 80:
            lines.append("3. 尝试调整软约束权重，适当放宽次要约束以换取整体方案质量提升。")
            lines.append("4. 检查课程连排设置是否合理，部分课程可能不需要严格连排。")

        if quality >= 90 and hard_count == 0:
            lines.append("当前方案已达到较优水平，建议在此基础上进行微量手动微调即可。")
            lines.append("可通过交互式甘特图对个别课程进行精细化调整。")

        return "\n".join(lines)
