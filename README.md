# 🌿 环境监测采样派单系统

环境监测采样派单管理系统 — 用于管理环境检测任务的录入、派单、人员调度与进度跟踪。

## 技术栈

| 层 | 技术 |
|---|------|
| 后端 | Python 3.13 + FastAPI + SQLAlchemy + SQLite |
| 前端 | 原生 JS SPA（单页应用），hash 路由 |
| 认证 | JWT（Bearer Token）+ 细粒度权限控制 |
| 部署 | systemd + uvicorn，端口 8080 |

## 功能

### 工作台
- 月度/季度/年度待派单统计卡片
- 今日任务（按采样组长分组）
- 本周任务概览（未完成/已完成/异常）
- 本月日历（标注节假日、调休、周末）

### 任务管理
- 新建/编辑/删除任务
- 项目类别：自行检测、委托检测、比对监测、验收检测
- 有效期：月度/季度/半年度/年度/组合（如月度+季度）
- 安徽省 16 市全部区县两级联动选择
- 检测类别：有组织排放、无组织排放、废(雨)水、地下水、噪声、土壤
- 筛选：状态、地区、有效期、搜索

### 派单计划
- 按月日历视图，按组长分组展示任务
- 自动定位到当前周
- 节假日/调休标注（数据源：[timor.tech](https://timor.tech/api/holiday/year/)）
- 工作日统计：工作日/周末/节假日
- 管理员可取消派单、改派任务

### 人员管理
- 添加/编辑/删除人员
- 组长-组员绑定（采样组员归属采样组长）
- 自动生成注册码（一键复制注册链接）
- 重置注册码

### 用户管理
- 管理员分权限创建用户
- 角色模板：系统管理员、现场部部长、采样组长、采样组员、报告部负责人、实验部负责人
- 细粒度权限控制（`admin_panel`、`manage_users`、`manage_tasks` 等）

## 快速开始

### 环境要求

- Python 3.10+
- pip

### 安装

```bash
# 克隆仓库
git clone https://github.com/kyri3m/XINGYUAN.git
cd XINGYUAN

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 安装依赖
pip install fastapi uvicorn sqlalchemy pyjwt passlib bcrypt python-multipart

# 启动服务
cd backend
python -m uvicorn main:app --host 0.0.0.0 --port 8080
```

### 默认管理员

- 用户名：`admin`
- 密码：`admin123`

> ⚠️ 首次启动自动创建管理员账号。请登录后立即修改密码。

### systemd 部署（Linux）

```bash
# 复制服务文件
sudo cp dispatch.service /etc/systemd/system/

# 启动并设置开机自启
sudo systemctl daemon-reload
sudo systemctl enable dispatch
sudo systemctl start dispatch

# 查看状态
sudo systemctl status dispatch
```

## 项目结构

```
├── backend/
│   ├── main.py          # FastAPI 入口 + 静态文件服务
│   ├── models.py        # SQLAlchemy 数据模型
│   ├── api.py           # REST API 路由
│   ├── auth.py          # JWT 认证 + 权限装饰器
│   └── schemas.py       # Pydantic 校验模型
├── frontend/
│   ├── index.html       # SPA 主页面（管理端）
│   ├── app5.js          # 前端核心逻辑
│   ├── login2.html      # 登录页
│   └── register.html    # 注册页
├── dispatch.service     # systemd 服务配置
├── README.md
└── .gitignore
```

## API 概览

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 登录获取 JWT |
| POST | `/api/auth/register` | 注册新用户 |
| GET | `/api/dashboard` | 工作台数据 |
| GET/POST | `/api/tasks` | 任务列表 / 新建 |
| PUT/DELETE | `/api/tasks/{id}` | 编辑 / 删除任务 |
| GET/POST | `/api/personnel` | 人员列表 / 添加 |
| PUT/DELETE | `/api/personnel/{id}` | 编辑 / 删除人员 |
| POST | `/api/personnel/{id}/regenerate-code` | 重置注册码 |
| GET | `/api/users` | 用户列表 |
| GET | `/api/meta/permissions` | 权限元数据 |

全部 API 需 `Authorization: Bearer <token>` 头部。

## 权限系统

| 权限键 | 说明 |
|--------|------|
| `admin_panel` | 进入管理端 |
| `manage_users` | 管理用户 |
| `manage_tasks` | 管理任务 |
| `view_all_tasks` | 查看全部任务 |
| `view_dispatch` | 查看派单计划 |
| `manage_personnel` | 管理人员 |
| `do_sampling` | 执行采样 |
| `manage_reports` | 管理报告 |
| `manage_lab` | 管理实验室 |

## 数据库

默认使用 SQLite（`backend/dispatch.db`），切换 MySQL 只需修改 `backend/models.py` 中的 `DATABASE_URL`：

```python
DATABASE_URL = "mysql+pymysql://user:password@localhost/dispatch"
```

## 地区数据

安徽省 16 市及全部区县，支持市→区县两级联动下拉选择。

## License

MIT
