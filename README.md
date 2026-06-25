# AI 驱动的一体化智能排课平台

基于**改进遗传算法**的多目标优化智能排课系统。前后端分离架构，支持课程、教师、班级、教室的全生命周期管理，自动生成满足硬约束、优化软约束的高质量课表方案。

---

## ✨ 核心功能

| 模块 | 功能 |
|------|------|
| 🔐 用户认证 | JWT 注册/登录，Token 24h 过期，受保护路由 |
| 📊 工作台 | 班级/教师/课程/教室实时统计 + 排课版本历史 |
| 📋 数据管理 | 班级、教师、课程、教室 CRUD + CSV 批量导入/教学大纲导入 |
| ⚙️ 约束配置 | 硬约束/软约束规则管理，支持历史数据学习优化权重 |
| 🧬 AI 排课 | 遗传算法多目标优化，支持选择排课范围、配置种群参数 |
| 📅 课表视图 | 甘特图课表，按班级/教师/教室三维度展示，支持拖拽调整 |
| ⚠️ 冲突检测 | 硬/软冲突自动检测，生成解决建议 |
| 📥 导入导出 | CSV 模板下载/导入，课表导出 Excel/PDF |

---

## 🛠 技术栈

| 层 | 技术 |
|---|------|
| 后端框架 | FastAPI 0.104 + Uvicorn |
| ORM | SQLAlchemy 2.0（自动建表） |
| 数据库 | SQLite（`backend/data/scheduling.db`） |
| 排课引擎 | 遗传算法 — NumPy + scikit-learn |
| 认证 | JWT（python-jose）+ PBKDF2 密码哈希 |
| 前端框架 | React 19 + TypeScript 6.0 |
| 构建工具 | Vite 8.1 |
| UI 组件库 | Ant Design 6.4（中文 locale） |
| 图表 | Recharts 3.9 |
| 拖拽 | @dnd-kit |
| 设计系统 | Stripe 风格紫色主题（`#533afd`） |

---

## 🚀 快速开始

### 环境要求

- **Python** 3.10+
- **Node.js** 18+
- **npm** 9+

### 1. 克隆项目

```bash
git clone https://github.com/lafeighb/AI-driven-intelligent-scheduling-platform.git
cd AI-driven-intelligent-scheduling-platform
```

### 2. 启动后端

```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端运行在 `http://localhost:8000`，首次启动自动创建 SQLite 数据库并建表。

API 文档：`http://localhost:8000/docs`

### 3. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端运行在 `http://localhost:5173`，通过 CORS 直接请求后端。

### 4. 开始使用

1. 打开 `http://localhost:5173`，注册账号并登录
2. 在「数据管理」中录入班级、教师、课程、教室
3. 在「约束配置」中设置排课规则
4. 进入「AI 智能排课」选择范围 → 配置参数 → 执行排课
5. 在「课表视图」中查看生成的课表方案

---

## 📐 排课引擎

### 算法架构

```
遗传算法 (GA)
├── 种群初始化 → 随机生成排课方案
├── 适应度评估 → 硬约束惩罚 + 软约束加权
├── 选择 → 锦标赛选择
├── 交叉 → 基于课程分组的均匀交叉
├── 变异 → 教师/教室/时间槽/班级/交换 五种策略
└── 早停 → 连续 N 代无改进且硬冲突为0时终止
```

### 约束体系

**硬约束（必须满足）：**
- 同一教师同一时间不能有两门课
- 同一教室同一时间不能有两门课
- 同一班级同一时间不能有两门课
- 教室容量不能超过上限的 120%
- 教师每周课时不超过上限
- 课程只能分配给匹配专业的班级
- 教师不可用时间段不能排课

**软约束（尽量满足）：**
- 教师时间偏好
- 课程时间分布均衡
- 班级每日课时均衡
- 教室利用率均衡

### 教师-课程匹配

排课前严格校验教师-课程匹配关系：
- 教师 `courses_can_teach` 明确列出课程 → 匹配
- 教师与课程 `department` 相同 → 匹配
- 以上都不满足 → **排课中断，提示用户分配教师**

---

## 📁 项目结构

```
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── main.py             # 应用入口，路由注册
│   │   ├── config.py           # 配置管理
│   │   ├── database.py         # 数据库引擎 + 会话
│   │   ├── models/             # ORM 模型
│   │   │   ├── user.py         # 用户
│   │   │   ├── class_info.py   # 班级
│   │   │   ├── teacher.py      # 教师
│   │   │   ├── course.py       # 课程
│   │   │   ├── classroom.py    # 教室
│   │   │   ├── schedule.py     # 排课条目
│   │   │   └── constraint.py   # 约束规则
│   │   ├── schemas/            # Pydantic 请求/响应模型
│   │   ├── api/                # API 路由
│   │   │   ├── auth.py         # 认证
│   │   │   ├── schedules.py    # 排课管理
│   │   │   └── import_export.py # 导入导出
│   │   ├── services/           # 业务逻辑
│   │   │   ├── scheduler.py    # 遗传算法排课引擎
│   │   │   ├── conflict.py     # 冲突检测器
│   │   │   ├── optimization.py # 约束学习服务
│   │   │   ├── explanation.py  # AI 优化说明生成
│   │   │   ├── export_service.py # Excel/PDF 导出
│   │   │   ├── validation.py   # 数据校验
│   │   │   └── auth.py         # JWT + 密码哈希
│   │   └── utils/
│   │       └── csv_parser.py   # CSV 解析器
│   ├── data/                   # SQLite 数据库文件
│   └── requirements.txt
│
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── main.tsx            # 入口
│   │   ├── App.tsx             # 路由配置
│   │   ├── theme.ts            # Ant Design 主题
│   │   ├── api/
│   │   │   └── client.ts       # Axios + API 函数 + JWT 拦截器
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx  # 认证状态管理
│   │   ├── components/
│   │   │   ├── AppLayout.tsx   # 应用布局
│   │   │   └── DataTable.tsx   # 通用表格组件
│   │   ├── pages/
│   │   │   ├── Login.tsx       # 登录
│   │   │   ├── Register.tsx    # 注册
│   │   │   ├── Dashboard.tsx   # 工作台
│   │   │   ├── TimetableView.tsx # 甘特图课表
│   │   │   ├── ExportPage.tsx  # 课表导出
│   │   │   ├── DataManagement/ # 数据管理（班级/教师/课程/教室/导入）
│   │   │   └── Scheduling/     # 排课管理（约束配置/引擎/冲突检测）
│   │   └── types/
│   │       └── index.ts        # TypeScript 类型定义
│   └── package.json
│
└── README.md
```

---

## 🔗 API 概览

| 方法 | 端点 | 说明 |
|------|------|------|
| POST | `/api/auth/register` | 用户注册 |
| POST | `/api/auth/login` | 用户登录 |
| GET | `/api/auth/me` | 获取当前用户 |
| GET/POST/PUT/DELETE | `/api/classes/` | 班级 CRUD |
| GET/POST/PUT/DELETE | `/api/teachers/` | 教师 CRUD |
| GET/POST/PUT/DELETE | `/api/courses/` | 课程 CRUD |
| GET/POST/PUT/DELETE | `/api/classrooms/` | 教室 CRUD |
| POST | `/api/schedules/generate` | AI 自动排课 |
| GET | `/api/schedules/` | 获取排课结果 |
| GET | `/api/schedules/versions` | 版本历史 |
| GET | `/api/schedules/conflicts` | 冲突检测 |
| GET | `/api/io/template/{type}` | 下载 CSV 模板 |
| POST | `/api/io/csv/{type}` | CSV 批量导入 |
| GET | `/api/io/export/{excel,pdf}` | 导出课表 |
| GET | `/api/io/report` | 分析报告 |

---

## 📄 License

MIT License

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)
