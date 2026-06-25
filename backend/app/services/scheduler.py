"""AI驱动多目标自动排课引擎 - 基于遗传算法的智能排课优化

核心算法: 改进型遗传算法(GA) + 多目标优化
支持约束: 硬约束(必须满足) + 软约束(尽量满足)
"""
import random
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Set
from copy import deepcopy
from dataclasses import dataclass, field
from collections import defaultdict
import json
import time
import uuid


# ========== 数据结构定义 ==========

@dataclass
class TimeSlot:
    """时间段"""
    day: int  # 1-5 (周一至周五)
    period: int  # 1-8 (节次)

    def __hash__(self):
        return hash((self.day, self.period))

    def __eq__(self, other):
        return self.day == other.day and self.period == other.period


@dataclass
class CourseAssignment:
    """课程分配 - 排课的基本单元（基因）"""
    course_id: int
    teacher_id: int
    class_id: int
    classroom_id: int
    time_slot: TimeSlot
    is_consecutive: bool = False  # 是否连排（连续2节）
    week_number: int = 1  # 教学周次

    def __hash__(self):
        return hash((self.course_id, self.teacher_id, self.class_id,
                    self.classroom_id, self.time_slot.day, self.time_slot.period))

    def to_dict(self) -> Dict:
        return {
            "course_id": self.course_id,
            "teacher_id": self.teacher_id,
            "class_id": self.class_id,
            "classroom_id": self.classroom_id,
            "day_of_week": self.time_slot.day,
            "period_start": self.time_slot.period,
            "period_end": self.time_slot.period + (1 if self.is_consecutive else 0),
            "week_number": self.week_number,
        }


@dataclass
class Schedule:
    """排课方案 - 一个完整的课表（个体/染色体）"""
    assignments: List[CourseAssignment] = field(default_factory=list)
    fitness: float = 0.0
    hard_violations: int = 0
    soft_violations: int = 0


# ========== 排课引擎 ==========

class SchedulingEngine:
    """改进型遗传算法排课引擎"""

    def __init__(self, config: Dict[str, Any] = None):
        """初始化排课引擎

        Args:
            config: 排课配置，包含算法参数和约束权重
        """
        self.config = {
            "population_size": 100,
            "max_generations": 500,
            "mutation_rate": 0.1,
            "crossover_rate": 0.8,
            "elite_count": 5,
            "tournament_size": 3,
            "early_stop_generations": 80,
            "early_stop_threshold": 0.001,
            # 约束权重
            "hard_penalty": 1000.0,  # 硬约束违反惩罚
            "soft_penalty_multiplier": 1.0,
            # 优化目标权重
            "weight_teacher_preference": 5.0,
            "weight_room_utilization": 3.0,
            "weight_time_distribution": 4.0,
            "weight_consecutive_reward": 2.0,
        }
        if config:
            self.config.update(config)

        # 数据存储
        self.courses: Dict[int, Dict] = {}
        self.teachers: Dict[int, Dict] = {}
        self.classes: Dict[int, Dict] = {}
        self.classrooms: Dict[int, Dict] = {}
        self.constraints: List[Dict] = []
        self.existing_schedule: List[Dict] = []

        # 课程-教师关联映射
        self.course_teacher_map: Dict[int, List[int]] = defaultdict(list)
        # 课程-班级关联映射（按 department 匹配）
        self.course_class_map: Dict[int, List[int]] = defaultdict(list)

        # 统计信息
        self.generation_history: List[Dict] = []
        self.best_schedule: Optional[Schedule] = None
        self.execution_time: float = 0.0

    def load_data(self, courses: List[Dict], teachers: List[Dict],
                  classes: List[Dict], classrooms: List[Dict],
                  constraints: List[Dict] = None,
                  existing_schedule: List[Dict] = None):
        """加载排课所需的基础数据"""
        self.courses = {c["id"]: c for c in courses}
        self.teachers = {t["id"]: t for t in teachers}
        self.classes = {c["id"]: c for c in classes}
        self.classrooms = {r["id"]: r for r in classrooms}
        self.constraints = constraints or []
        self.existing_schedule = existing_schedule or []

        # 构建课程-教师关联：从教师数据中解析可教课程，或基于部门匹配
        self._build_course_teacher_map()
        # 构建课程-班级关联：基于 department 字段匹配
        self._build_course_class_map()

    def _build_course_teacher_map(self):
        """构建课程-教师关联映射"""
        self.course_teacher_map.clear()
        for course_id, course in self.courses.items():
            dept = course.get("department", "")
            for teacher_id, teacher in self.teachers.items():
                # 检查教师的 courses_can_teach 字段
                can_teach = teacher.get("courses_can_teach")
                if can_teach:
                    try:
                        teach_list = json.loads(can_teach) if isinstance(can_teach, str) else can_teach
                        if course_id in teach_list or str(course_id) in [str(x) for x in teach_list]:
                            self.course_teacher_map[course_id].append(teacher_id)
                            continue
                    except (json.JSONDecodeError, TypeError):
                        pass
                # 基于部门匹配（同部门的教师可以教同部门的课程）
                teacher_dept = teacher.get("department", "")
                if dept and teacher_dept and dept == teacher_dept:
                    if teacher_id not in self.course_teacher_map[course_id]:
                        self.course_teacher_map[course_id].append(teacher_id)

        # 如果没有匹配到任何教师，给每个课程分配所有教师
        all_teacher_ids = list(self.teachers.keys())
        for course_id in self.courses:
            if not self.course_teacher_map[course_id]:
                self.course_teacher_map[course_id] = all_teacher_ids.copy()

    def _build_course_class_map(self):
        """构建课程-班级关联映射：基于 department 字段匹配

        规则：
        - 课程有 department 且班级有相同 department → 匹配
        - 课程没有 department（通用课）→ 匹配所有班级
        - 班级没有 department → 匹配所有课程
        - department 不匹配 → 不分配
        """
        self.course_class_map.clear()
        all_class_ids = list(self.classes.keys())

        for course_id, course in self.courses.items():
            course_dept = (course.get("department") or "").strip()
            if not course_dept:
                # 通用课程，可分配给所有班级
                self.course_class_map[course_id] = all_class_ids.copy()
                continue

            eligible = []
            for class_id, cls in self.classes.items():
                class_dept = (cls.get("department") or "").strip()
                if not class_dept or class_dept == course_dept:
                    eligible.append(class_id)

            self.course_class_map[course_id] = eligible if eligible else all_class_ids.copy()

    def generate_initial_population(self) -> List[Schedule]:
        """生成初始种群"""
        population = []
        for _ in range(self.config["population_size"]):
            schedule = self._create_random_schedule()
            population.append(schedule)
        return population

    def _create_random_schedule(self) -> Schedule:
        """创建随机排课方案"""
        assignments = []
        days = list(range(1, self.config.get("weekdays", 5) + 1))
        periods = list(range(1, self.config.get("periods_per_day", 8) + 1))

        # 获取所有可用的时间槽
        all_slots = []
        for day in days:
            for period in periods:
                all_slots.append(TimeSlot(day, period))

        for course_id, course in self.courses.items():
            weekly_hours = course.get("weekly_hours", 2)
            needs_consecutive = course.get("requires_consecutive", False)

            # 获取可教授该课程的教师
            eligible_teachers = self.course_teacher_map.get(course_id, list(self.teachers.keys()))
            if not eligible_teachers:
                continue

            # 获取可用的教室
            eligible_rooms = list(self.classrooms.keys())
            if course.get("requires_lab"):
                eligible_rooms = [r_id for r_id, r in self.classrooms.items()
                                 if "实验室" in r.get("room_type", "") or "机房" in r.get("room_type", "")]
            if not eligible_rooms:
                eligible_rooms = list(self.classrooms.keys())

            # 随机选择时间槽
            random.shuffle(all_slots)
            assigned_hours = 0

            for slot in all_slots:
                if assigned_hours >= weekly_hours:
                    break

                # 连排课程需要使用连续的节次
                if needs_consecutive:
                    next_slot = TimeSlot(slot.day, slot.period + 1)
                    if slot.period >= periods[-1] or not any(
                            s.day == next_slot.day and s.period == next_slot.period for s in all_slots):
                        continue
                    is_consecutive = True
                    assigned_hours += 2
                else:
                    is_consecutive = False
                    assigned_hours += 1

                # 获取该课程可分配的目标班级（按 department 匹配）
                eligible_classes = self.course_class_map.get(course_id, list(self.classes.keys()))
                if not eligible_classes:
                    eligible_classes = list(self.classes.keys())

                # 检查时间段是否已被占用
                assignment = CourseAssignment(
                    course_id=course_id,
                    teacher_id=random.choice(eligible_teachers),
                    class_id=random.choice(eligible_classes),
                    classroom_id=random.choice(eligible_rooms),
                    time_slot=slot,
                    is_consecutive=is_consecutive,
                    week_number=random.randint(1, 20)
                )
                assignments.append(assignment)

        schedule = Schedule(assignments=assignments)
        self._evaluate_fitness(schedule)
        return schedule

    def _evaluate_fitness(self, schedule: Schedule):
        """评估排课方案的适应度（核心评估函数）

        适应度 = - (硬约束违反数 * 硬惩罚 + 软约束违反加权和)
        适应度越高 = 方案越好 = 违反越少
        """
        hard_violations = 0
        soft_violations = 0
        soft_penalty_sum = 0.0

        # === 硬约束检查 ===

        # 1. 同一教师同一时间不能有两门课
        teacher_slot_map: Dict[Tuple[int, int, int], int] = defaultdict(int)
        for a in schedule.assignments:
            key = (a.teacher_id, a.time_slot.day, a.time_slot.period)
            teacher_slot_map[key] += 1
            # 连排也要检查下一节
            if a.is_consecutive:
                key2 = (a.teacher_id, a.time_slot.day, a.time_slot.period + 1)
                teacher_slot_map[key2] += 1

        hard_violations += sum(max(0, v - 1) for v in teacher_slot_map.values())

        # 2. 同一教室同一时间不能有两门课
        room_slot_map: Dict[Tuple[int, int, int], int] = defaultdict(int)
        for a in schedule.assignments:
            key = (a.classroom_id, a.time_slot.day, a.time_slot.period)
            room_slot_map[key] += 1
            if a.is_consecutive:
                key2 = (a.classroom_id, a.time_slot.day, a.time_slot.period + 1)
                room_slot_map[key2] += 1

        hard_violations += sum(max(0, v - 1) for v in room_slot_map.values())

        # 3. 同一班级同一时间不能有两门课
        class_slot_map: Dict[Tuple[int, int, int], int] = defaultdict(int)
        for a in schedule.assignments:
            key = (a.class_id, a.time_slot.day, a.time_slot.period)
            class_slot_map[key] += 1
            if a.is_consecutive:
                key2 = (a.class_id, a.time_slot.day, a.time_slot.period + 1)
                class_slot_map[key2] += 1

        hard_violations += sum(max(0, v - 1) for v in class_slot_map.values())

        # 4. 教室容量检查（硬约束：不能超员）
        for a in schedule.assignments:
            classroom = self.classrooms.get(a.classroom_id, {})
            class_info = self.classes.get(a.class_id, {})
            if classroom.get("capacity") and class_info.get("student_count"):
                if class_info["student_count"] > classroom["capacity"] * 1.2:
                    hard_violations += 1

        # 5. 教师每周课时上限
        teacher_weekly_hours: Dict[int, int] = defaultdict(int)
        for a in schedule.assignments:
            teacher_weekly_hours[a.teacher_id] += 2 if a.is_consecutive else 1
        for t_id, hours in teacher_weekly_hours.items():
            max_hours = self.teachers.get(t_id, {}).get("max_weekly_hours", 20)
            if max_hours and hours > max_hours:
                hard_violations += (hours - max_hours)

        # 6. 课程-班级部门匹配检查（硬约束：课程必须分配到匹配专业的班级）
        for a in schedule.assignments:
            eligible = self.course_class_map.get(a.course_id, [])
            if eligible and a.class_id not in eligible:
                hard_violations += 5  # 部门不匹配视为较严重违规

        # === 软约束检查 ===

        # 1. 教师时间偏好
        for a in schedule.assignments:
            teacher = self.teachers.get(a.teacher_id, {})
            preferred = teacher.get("preferred_time_slots")
            if preferred:
                try:
                    pref_slots = json.loads(preferred) if isinstance(preferred, str) else preferred
                    slot_key = f"{a.time_slot.day}-{a.time_slot.period}"
                    if slot_key not in pref_slots and pref_slots:
                        soft_violations += 1
                        soft_penalty_sum += self.config["weight_teacher_preference"] * 0.5
                except (json.JSONDecodeError, TypeError):
                    pass

            # 2. 检查教师不可用时间
            unavailable = teacher.get("unavailable_slots")
            if unavailable:
                try:
                    unavail = json.loads(unavailable) if isinstance(unavailable, str) else unavailable
                    slot_key = f"{a.time_slot.day}-{a.time_slot.period}"
                    if slot_key in unavail:
                        hard_violations += 3  # 教师不可用时间算作严重违规
                except (json.JSONDecodeError, TypeError):
                    pass

        # 3. 课程时间分布（避免同一天过多集中）
        course_day_map: Dict[Tuple[int, int], int] = defaultdict(int)
        for a in schedule.assignments:
            course_day_map[(a.course_id, a.time_slot.day)] += 1
        for (c_id, day), count in course_day_map.items():
            if count > 2:  # 同一门课同一天超过2节
                soft_violations += (count - 2)
                soft_penalty_sum += self.config["weight_time_distribution"] * (count - 2)

        # 4. 班级每日课时均衡
        class_day_hours: Dict[Tuple[int, int], int] = defaultdict(int)
        for a in schedule.assignments:
            class_day_hours[(a.class_id, a.time_slot.day)] += 2 if a.is_consecutive else 1
        for c_id in self.classes:
            day_hours = [class_day_hours.get((c_id, d), 0) for d in range(1, 6)]
            if day_hours and max(day_hours) > 0:
                variance = np.var(day_hours) if len(day_hours) > 1 else 0
                soft_penalty_sum += variance * self.config["weight_time_distribution"] * 0.5

        # 5. 教室利用率均衡
        room_day_usage: Dict[Tuple[int, int], int] = defaultdict(int)
        for a in schedule.assignments:
            room_day_usage[(a.classroom_id, a.time_slot.day)] += 1
        for r_id in self.classrooms:
            day_usage = [room_day_usage.get((r_id, d), 0) for d in range(1, 6)]
            if day_usage and max(day_usage) > 0:
                variance = np.var(day_usage) if len(day_usage) > 1 else 0
                soft_penalty_sum += variance * self.config["weight_room_utilization"] * 0.3

        # 计算总适应度（越高越好）
        total_penalty = (hard_violations * self.config["hard_penalty"] +
                        soft_penalty_sum * self.config["soft_penalty_multiplier"])

        schedule.hard_violations = hard_violations
        schedule.soft_violations = soft_violations
        schedule.fitness = -total_penalty  # 负值，越接近0越好

    def _selection(self, population: List[Schedule]) -> Schedule:
        """锦标赛选择"""
        tournament = random.sample(population, min(self.config["tournament_size"], len(population)))
        return max(tournament, key=lambda s: s.fitness)

    def _crossover(self, parent1: Schedule, parent2: Schedule) -> Tuple[Schedule, Schedule]:
        """交叉操作 - 基于课程分组的均匀交叉"""
        if random.random() > self.config["crossover_rate"]:
            return deepcopy(parent1), deepcopy(parent2)

        child1 = Schedule()
        child2 = Schedule()

        # 按课程分组
        p1_by_course: Dict[int, List[CourseAssignment]] = defaultdict(list)
        p2_by_course: Dict[int, List[CourseAssignment]] = defaultdict(list)
        for a in parent1.assignments:
            p1_by_course[a.course_id].append(a)
        for a in parent2.assignments:
            p2_by_course[a.course_id].append(a)

        all_courses = set(list(p1_by_course.keys()) + list(p2_by_course.keys()))

        for course_id in all_courses:
            if random.random() < 0.5:
                child1.assignments.extend(deepcopy(p1_by_course.get(course_id, [])))
                child2.assignments.extend(deepcopy(p2_by_course.get(course_id, [])))
            else:
                child1.assignments.extend(deepcopy(p2_by_course.get(course_id, [])))
                child2.assignments.extend(deepcopy(p1_by_course.get(course_id, [])))

        for child in [child1, child2]:
            self._evaluate_fitness(child)

        return child1, child2

    def _mutation(self, schedule: Schedule):
        """变异操作"""
        if not schedule.assignments:
            return schedule

        for i, assignment in enumerate(schedule.assignments):
            if random.random() < self.config["mutation_rate"]:
                # 随机选择变异类型
                mutation_type = random.choice(["teacher", "classroom", "timeslot", "class", "swap"])

                if mutation_type == "teacher":
                    eligible = self.course_teacher_map.get(assignment.course_id, [])
                    if eligible:
                        assignment.teacher_id = random.choice(eligible)

                elif mutation_type == "classroom":
                    course = self.courses.get(assignment.course_id, {})
                    eligible = list(self.classrooms.keys())
                    if course.get("requires_lab"):
                        lab_rooms = [r_id for r_id, r in self.classrooms.items()
                                    if "实验室" in r.get("room_type", "") or "机房" in r.get("room_type", "")]
                        if lab_rooms:
                            eligible = lab_rooms
                    if eligible:
                        assignment.classroom_id = random.choice(eligible)

                elif mutation_type == "class":
                    eligible = self.course_class_map.get(assignment.course_id, list(self.classes.keys()))
                    if eligible and len(eligible) > 1:
                        current = assignment.class_id
                        others = [c for c in eligible if c != current]
                        if others:
                            assignment.class_id = random.choice(others)

                elif mutation_type == "timeslot":
                    days = list(range(1, self.config.get("weekdays", 5) + 1))
                    max_period = self.config.get("periods_per_day", 8)
                    assignment.time_slot = TimeSlot(
                        day=random.choice(days),
                        period=random.randint(1, max_period - (1 if assignment.is_consecutive else 0))
                    )

                elif mutation_type == "swap" and len(schedule.assignments) > 1:
                    # 随机交换两个分配的时间槽
                    j = random.randint(0, len(schedule.assignments) - 1)
                    if i != j:
                        other = schedule.assignments[j]
                        assignment.time_slot, other.time_slot = other.time_slot, assignment.time_slot
                        assignment.classroom_id, other.classroom_id = other.classroom_id, assignment.classroom_id

        self._evaluate_fitness(schedule)
        return schedule

    def run(self, progress_callback=None) -> Dict[str, Any]:
        """运行遗传算法排课

        Args:
            progress_callback: 进度回调函数，接收(当前代数, 最佳适应度, 平均适应度)

        Returns:
            排课结果字典
        """
        start_time = time.time()
        self.generation_history = []

        # 生成初始种群
        population = self.generate_initial_population()

        best_fitness_history = []
        generations_no_improve = 0

        for gen in range(self.config["max_generations"]):
            # 评估所有个体
            for schedule in population:
                if schedule.fitness == 0 and schedule.hard_violations == 0:
                    self._evaluate_fitness(schedule)

            # 按适应度排序
            population.sort(key=lambda s: s.fitness, reverse=True)
            current_best = population[0]

            # 记录历史
            avg_fitness = np.mean([s.fitness for s in population])
            self.generation_history.append({
                "generation": gen,
                "best_fitness": current_best.fitness,
                "avg_fitness": float(avg_fitness),
                "hard_violations": current_best.hard_violations,
                "soft_violations": current_best.soft_violations,
            })

            # 进度回调
            if progress_callback:
                progress_callback(gen, current_best.fitness, avg_fitness)

            # 早停检查
            best_fitness_history.append(current_best.fitness)
            if len(best_fitness_history) > 1:
                if abs(best_fitness_history[-1] - best_fitness_history[-2]) < self.config["early_stop_threshold"]:
                    generations_no_improve += 1
                else:
                    generations_no_improve = 0

            if (generations_no_improve >= self.config["early_stop_generations"]
                    and current_best.hard_violations == 0):
                break

            # 创建下一代
            new_population = []

            # 精英保留
            elite_count = min(self.config["elite_count"], len(population))
            for i in range(elite_count):
                new_population.append(deepcopy(population[i]))

            # 生成新个体
            while len(new_population) < self.config["population_size"]:
                parent1 = self._selection(population)
                parent2 = self._selection(population)
                child1, child2 = self._crossover(parent1, parent2)

                self._mutation(child1)
                self._mutation(child2)

                new_population.append(child1)
                if len(new_population) < self.config["population_size"]:
                    new_population.append(child2)

            population = new_population

        # 最终排序
        population.sort(key=lambda s: s.fitness, reverse=True)
        self.best_schedule = population[0]
        self.execution_time = time.time() - start_time

        return self._build_result()

    def _build_result(self) -> Dict[str, Any]:
        """构建排课结果"""
        if not self.best_schedule:
            return {"success": False, "error": "未能生成有效排课方案"}

        entries = []
        for a in self.best_schedule.assignments:
            entry = {
                "course_id": a.course_id,
                "teacher_id": a.teacher_id,
                "class_id": a.class_id,
                "classroom_id": a.classroom_id,
                "day_of_week": a.time_slot.day,
                "period_start": a.time_slot.period,
                "period_end": a.time_slot.period + (1 if a.is_consecutive else 0),
                "week_number": a.week_number,
                "is_consecutive": a.is_consecutive,
                "course_name": self.courses.get(a.course_id, {}).get("name", ""),
                "teacher_name": self.teachers.get(a.teacher_id, {}).get("name", ""),
                "class_name": self.classes.get(a.class_id, {}).get("name", ""),
                "classroom_name": self.classrooms.get(a.classroom_id, {}).get("name", ""),
            }
            entries.append(entry)

        # 计算质量评分 (0-100)
        max_possible_fitness = 0  # 最佳情况适应度为0
        min_possible_fitness = -10000  # 假设最差情况
        fitness = self.best_schedule.fitness
        quality_score = max(0, min(100, 100 * (1 - abs(fitness) / abs(min_possible_fitness))))

        return {
            "success": True,
            "version": f"schedule_{int(time.time())}_{uuid.uuid4().hex[:8]}",
            "total_entries": len(entries),
            "hard_conflicts": self.best_schedule.hard_violations,
            "soft_conflicts": self.best_schedule.soft_violations,
            "quality_score": round(quality_score, 1),
            "execution_time": round(self.execution_time, 2),
            "algorithm": f"遗传算法(GA) - 种群{self.config['population_size']}, 进化{len(self.generation_history)}代",
            "generation_history": self.generation_history[-10:],  # 最后10代历史
            "entries": entries,
        }
