# 星源 · 环境监测协作平台

环境监测任务录入、派单、人员协作和采样记录管理系统。新版采用模块化 FastAPI 后端和原生 ES Modules 前端，支持中文桌面与移动布局。

## 本机访问

- 地址：http://127.0.0.1:8080
- 初始账号：`admin`
- 初始密码：`admin123`
- 登录后点击右上角盾牌按钮修改密码。
- 首次启动只创建管理员。业务数据为空，可先添加采样人员，再创建任务和派单。

## 启动与停止（Windows PowerShell）

在项目根目录执行：

```powershell
./start.ps1
./stop.ps1
```

启动脚本使用项目 `.venv`，在后台启动服务，检查健康状态并保存进程记录。仅监听本机回环地址，不开放局域网或公网访问；没有设置开机自启。

前台启动：

```powershell
./.venv/Scripts/python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8080
```

在另一台电脑首次安装（Python 3.12+）：

```powershell
python -m venv .venv
./.venv/Scripts/python.exe -m pip install -r requirements.txt
./start.ps1
```

前端无需安装 npm 依赖或编译。HTML、CSS 与 JavaScript 由后端同源提供。

## 功能

- 工作台：实时统计、日期任务、异常关注、完成率与团队负载。
- 任务管理：增删改查、状态/关键词/地区/有效期筛选、分页、CSV 导出。
- 派单：多组长和组员安排、月历、改派、日期及人员冲突检查。
- 采样：点位记录、现场说明、完成/异常/取消及实际工时。
- 人员：组长与组员绑定、注册码邀请、资料编辑、关联数据保护。
- 账号：角色模板、细粒度权限、账号停用、密码修改和越权保护。
- 安全：任务归属精确判定、输入校验、随机 JWT 密钥、动态文本转义。

## 架构

```text
backend/
  main.py           应用入口、静态资源、健康检查
  config.py         路径、数据库 URL、JWT 密钥
  database.py       会话与 SQLAlchemy Base
  permissions.py    权限词表与角色模板
  models.py         兼容原数据库的领域模型
  schemas.py        请求及响应模型
  services.py       任务授权与业务校验
  api.py            路由组合
  routes/           认证、用户、人员、任务、采样、统计
frontend/
  index.html        应用入口
  styles.css        设计变量、组件、响应式布局
  js/api.js         API 请求与会话
  js/ui.js          转义、图标、表单与对话框
  js/views.js       工作台、表格、日历与管理视图
  js/forms.js       任务、派单、采样、人员、用户操作
  js/app.js         状态、路由和事件编排
  js/regions.js     原仓库安徽地区数据
```

## 数据与配置

数据库默认位于 `backend/dispatch.db`；原表结构保留。运行数据、随机密钥和服务日志位于 `data/`。备份时停止服务，复制数据库及 `data/.jwt-secret`。删除密钥文件将使已有会话失效。

可通过环境变量覆盖 `DATABASE_URL`、`JWT_SECRET`、`ADMIN_PASSWORD`；见 `.env.example`。`ADMIN_PASSWORD` 只在首次创建管理员时使用，不会覆盖已有密码。

## 验证

```powershell
./.venv/Scripts/python.exe -m pytest -q
node tests/ui.mjs
```

API 测试使用独立内存数据库，不会写入本地业务数据。接口文档：http://127.0.0.1:8080/docs 。健康检查：`GET /api/health`。

审阅结果、修复项、验证范围与已知边界见 [REVIEW.md](REVIEW.md)。本地上游源码快照、运行数据及密钥不纳入版本控制。

完整验收测试结果（26 项后端测试、12 项前端逻辑检查及真实页面操作）见 [TEST-REPORT.md](TEST-REPORT.md)。
