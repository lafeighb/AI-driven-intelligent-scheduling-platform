# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

AI 驱动的一体化智能排课平台 — 基于改进遗传算法的多目标优化排课系统。前后端分离架构：FastAPI 后端 + React 前端，使用 SQLite 数据库。

## 启动命令

```bash
# 后端（Python 3.14，端口 8000）
cd backend
/c/Python314/python.exe -m pip install -r requirements.txt
/c/Python314/python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 前端（Node.js 18+，端口 5173）
cd frontend
npm install
npm run dev
```

前端默认运行在 `http://localhost:5173`，预计后端在 `http://localhost:8000`。前端直接跨域请求后端，未配置 Vite 代理。后端 CORS 白名单为 `localhost:5173` 和 `localhost:3000`。

## 技术栈

| 层 | 技术 |
|---|------|
| 后端框架 | FastAPI 0.104 + Uvicorn |
| ORM | SQLAlchemy 2.0（自动建表，无需迁移工具） |
| 数据库 | SQLite（文件：`backend/data/scheduling.db`） |
| 排课引擎 | 遗传算法（numpy + scikit-learn） |
| 认证 | JWT（python-jose）+ PBKDF2 密码哈希 |
| 前端框架 | React 19 + TypeScript 6.0 |
| 构建工具 | Vite 8.1 |
| UI 组件库 | Ant Design 6.4（中文 locale） |
| 图表 | Recharts 3.9 |
| 拖拽 | @dnd-kit |
| 设计系统 | Stripe 风格（紫色 `#533afd` 主题） |

## 架构

### 后端分层

```
backend/app/
├── main.py              # FastAPI 入口，注册路由，lifespan 中 init_db()
├── config.py            # Pydantic Settings（DATABASE_URL, CORS, 遗传参数默认值）
├── database.py          # SQLAlchemy 引擎、SessionLocal、Base、get_db 依赖
├── models/              # ORM 模型（均继承 Base + TimestampMixin）
│   ├── user.py          # User（username, email, password_hash, is_active）
│   ├── class_info.py    # ClassInfo
│   ├── teacher.py       # Teacher
│   ├── course.py        # Course
│   ├── classroom.py     # Classroom
│   ├── schedule.py      # ScheduleEntry（含 schedule_version 字段）
│   └── constraint.py    # ConstraintRule
├── schemas/             # Pydantic 请求/响应模型
├── api/                 # 路由处理（每个资源一个文件）
│   ├── auth.py          # POST /register, POST /login, GET /me
│   ├── schedules.py     # POST /generate, GET /, GET /versions, 冲突检测等
│   └── import_export.py # 导出 Excel/PDF, GET /io/report
├── services/            # 业务逻辑
│   ├── scheduler.py     # 遗传算法排课引擎（SchedulingEngine）
│   ├── conflict.py      # ConflictDetector（硬/软冲突检测）
│   ├── optimization.py  # ConstraintLearningService
│   ├── explanation.py   # AI 优化说明生成
│   ├── export_service.py # Excel/PDF 导出 + 分析报告生成
│   ├── validation.py    # 数据校验
│   └── auth.py          # JWT 令牌 + 密码哈希 + get_current_user/require_user 依赖
└── utils/
    └── csv_parser.py    # CSV 批量导入
```

**关键模式：**
- 所有路由前缀为 `/api/<resource>/`，在 `main.py` 中通过 `app.include_router()` 注册
- 数据库会话通过 `Depends(get_db)` 注入
- `_enrich_entry()` 函数在返回排课条目时 JOIN 获取关联实体名称（course_name, teacher_name 等）
- 版本字符串格式：`schedule_{unix_timestamp}_{uuid8}`，在 `scheduler.py` 的 `_build_result()` 中生成
- `init_db()` 在应用启动时调用 `Base.metadata.create_all()` 自动建表

### 前端分层

```
frontend/src/
├── main.tsx             # 入口
├── App.tsx              # 路由配置（AuthProvider → BrowserRouter → Routes）
├── theme.ts             # Ant Design 主题 token（Stripe 风格）
├── api/
│   └── client.ts        # Axios 实例 + 所有 API 函数 + JWT 拦截器
├── contexts/
│   └── AuthContext.tsx   # 认证状态管理（login/register/logout + token 持久化）
├── components/
│   ├── AppLayout.tsx    # 侧边栏 + 头部 + 内容区布局
│   └── DataTable.tsx    # 通用数据表格
├── pages/
│   ├── Login.tsx        # 登录页
│   ├── Register.tsx     # 注册页
│   ├── Dashboard.tsx    # 工作台（统计卡片 + 版本记录 + 分析报告整合）
│   ├── TimetableView.tsx # 甘特图课表视图（支持 ?version= 参数）
│   ├── ExportPage.tsx   # 课表导出
│   ├── DataManagement/  # 班级/教师/课程/教室 CRUD + 数据导入
│   └── Scheduling/      # 约束配置 / 执行排课 / 冲突检测
└── types/
    └── index.ts         # 所有 TypeScript 接口定义
```

**关键模式：**
- `AppLayout` 通过 `<Outlet />` 渲染子路由，侧边栏 `menuItems` 数组驱动导航
- 所有受保护路由包裹在 `<ProtectedRoute>` 中，未登录重定向 `/login`
- `AuthContext` 读取 `localStorage.access_token`，启动时调用 `GET /api/auth/me` 验证
- API 客户端 `baseURL` 硬编码为 `http://localhost:8000/api`
- 响应拦截器对 401 自动清除 token 并跳转登录页
- 导出 API 使用 `responseType: 'blob'`，响应拦截器只解包 `response.data`

### 认证流程

1. 注册/登录 → 后端返回 `{ access_token, user }` → 前端存入 `localStorage.access_token` + AuthContext
2. 每次请求通过 Axios 拦截器自动携带 `Authorization: Bearer <token>`
3. 后端 `require_user` 依赖解析 JWT 并查询 `users` 表
4. Token 24 小时过期

### 排课流程

1. 用户录入基础数据（班级/教师/课程/教室）
2. 配置约束规则（硬约束/软约束，可学习历史数据优化权重）
3. 执行排课 → `POST /api/schedules/generate` → 遗传算法运行 → 生成方案
4. 冲突检测 → 硬冲突必须解决、软冲突可接受
5. 课表视图按班级/教师/教室三维度展示
6. 导出 Excel/PDF

## 重要注意事项

- 数据库文件 `backend/data/scheduling.db` 由 SQLAlchemy 自动创建，首次启动时自动建表
- 前端使用 Ant Design 6.x，部分 API 已废弃（`bordered` → `variant`，`valueStyle` → `styles.content`，`bodyStyle` → `styles.body`，`headStyle` → `styles.header`）
- 前端未配置 Vite 代理，依赖后端 CORS 中间件处理跨域
- `ReportsPage.tsx` 路由已移除（内容整合到 Dashboard），但文件仍存在于目录中
- 导出端点 `GET /api/io/export/{excel,pdf}` 不需要认证（未添加 `Depends(require_user)`）
- 分析报告的 `quality_score` 在 `import_export.py` 报告端点中被硬编码为 85.0
