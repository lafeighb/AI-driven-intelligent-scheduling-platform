// ===== 用户认证类型 =====
export interface UserInfo {
  id: number;
  username: string;
  email: string;
  is_active: boolean;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: UserInfo;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
}

// ===== 基础实体类型 =====
export interface ClassInfo {
  id: number;
  name: string;
  grade: string;
  student_count: number;
  department?: string;
  homeroom_teacher?: string;
  remarks?: string;
  created_at: string;
  updated_at: string;
}

export interface Teacher {
  id: number;
  name: string;
  teacher_code: string;
  department?: string;
  title?: string;
  email?: string;
  phone?: string;
  max_weekly_hours?: number;
  preferred_time_slots?: string;
  courses_can_teach?: string;
  unavailable_slots?: string;
  remarks?: string;
  created_at: string;
  updated_at: string;
}

export interface Course {
  id: number;
  name: string;
  course_code: string;
  course_type: string;
  semester_sessions: number;
  weekly_sessions: number;
  hours_per_session: number;
  total_hours?: number;
  credits?: number;
  requires_consecutive: boolean;
  requires_lab: boolean;
  priority: number;
  department?: string;
  remarks?: string;
  created_at: string;
  updated_at: string;
}

export interface Classroom {
  id: number;
  name: string;
  room_code: string;
  building?: string;
  floor?: number;
  capacity: number;
  room_type: string;
  has_multimedia: boolean;
  is_available: boolean;
  remarks?: string;
  created_at: string;
  updated_at: string;
}

// ===== 班级/教师课程视图类型 =====
export interface ClassCourseInfo {
  course_id: number;
  course_name: string;
  course_code: string;
  semester_sessions: number;
  weekly_sessions: number;
  hours_per_session: number;
  total_hours?: number;
  teacher_names: string[];
  time_slots: number;
}

export interface ClassCoursesResponse {
  class_id: number;
  class_name: string;
  grade: string;
  department?: string;
  courses: ClassCourseInfo[];
  total_weekly_hours: number;
}

export interface TeacherCourseInfo {
  course_id: number;
  course_name: string;
  course_code: string;
  semester_sessions: number;
  weekly_sessions: number;
  hours_per_session: number;
  total_hours?: number;
  class_name: string;
  time_slots: number;
}

export interface TeacherCoursesResponse {
  teacher_id: number;
  teacher_name: string;
  department?: string;
  title?: string;
  courses: TeacherCourseInfo[];
  total_weekly_hours: number;
}

// ===== 排课版本类型 =====
export interface VersionInfo {
  version: string;
  entry_count: number;
  avg_quality?: number;
  timestamp?: number;  // Unix 秒级时间戳
}

// ===== 排课相关类型 =====
export interface ScheduleEntry {
  id: number;
  course_id: number;
  teacher_id: number;
  class_id: number;
  classroom_id: number;
  week_number: number;
  day_of_week: number;
  period_start: number;
  period_end: number;
  status: string;
  is_manual: boolean;
  quality_score?: number;
  schedule_version?: string;
  course_name?: string;
  teacher_name?: string;
  class_name?: string;
  classroom_name?: string;
  created_at: string;
  updated_at: string;
}

export interface ScheduleRequest {
  schedule_version?: string;
  class_ids?: number[];
  teacher_ids?: number[];
  course_ids?: number[];
  week_range?: number[];
  algorithm?: string;
  population_size?: number;
  max_generations?: number;
}

export interface ScheduleResult {
  success: boolean;
  version: string;
  total_entries: number;
  hard_conflicts: number;
  soft_conflicts: number;
  quality_score: number;
  explanation: string;
  entries: ScheduleEntry[];
}

export interface ConflictInfo {
  conflict_type: 'hard' | 'soft';
  category: string;
  description: string;
  severity: number;
  entries_involved: number[];
  resolution_suggestion?: string;
}

// ===== 约束规则类型 =====
export interface ConstraintRule {
  id: number;
  name: string;
  description?: string;
  rule_type: 'hard' | 'soft';
  category: string;
  rule_expression?: string;
  weight: number;
  penalty_score: number;
  is_active: boolean;
  priority: number;
  learned_from_history: boolean;
  satisfaction_rate?: number;
  conflict_severity?: number;
  created_at: string;
  updated_at: string;
}

export interface ConstraintLearningResult {
  rule_id: number;
  rule_name: string;
  satisfaction_rate: number;
  conflict_count: number;
  conflict_severity_mean: number;
  impact_on_quality: number;
  recommendation: string;
}

// ===== 分析报告类型 =====
export interface AnalysisReport {
  report_time: string;
  schedule_version: string;
  quality_score: number;
  execution_time: number;
  summary: {
    total_entries: number;
    unique_courses: number;
    unique_teachers: number;
    unique_classes: number;
    unique_classrooms: number;
    hard_conflicts: number;
    soft_conflicts: number;
  };
  daily_distribution: Record<string, number>;
  daily_balance_score: number;
  room_utilization: Record<string, { total_slots_used: number; utilization_rate: number }>;
  avg_room_utilization: number;
  teacher_workload: Record<string, number>;
  avg_teacher_workload: number;
  ai_explanation: string;
  constraint_learning: string;
  conflict_summary: {
    hard_by_category: Record<string, number>;
    soft_by_category: Record<string, number>;
  };
}

// ===== 导入导出类型 =====
export interface ImportResult {
  success: boolean;
  imported: number;
  total: number;
  errors: string[];
  warnings: string[];
  summary: string;
}

export interface ValidationResult {
  total: number;
  valid: number;
  invalid: number;
  errors: { row: number; field: string; message: string }[];
  warnings: { row: number; field: string; message: string; severity: string }[];
  summary: string;
}
