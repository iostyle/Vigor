# Vigor 快速运行设计

## 背景

Vigor 由 `vigor-server` 和 `vigor-client` 两部分组成。后端依赖 PostgreSQL、Redis、Alembic、FastAPI、Celery worker 和 Celery beat；前端依赖 Vite。新设备 clone 后如果逐项启动，容易遗漏环境变量、迁移或后台任务进程。

## 目标

提供一条适合开发环境的快速启动路径：新设备安装基础工具后，在仓库根目录执行一个命令即可启动数据库、Redis、后端、Celery 和前端，并能通过文档快速定位常见问题。

## 非目标

- 不在本次实现生产部署方案。
- 不强制全容器化前后端。
- 不内置真实抖音、豆包或 B 站登录凭证。
- 不自动清空数据库数据。

## 推荐方案

采用“Docker 基础服务 + 本机开发进程”的方案：

- Docker Compose 只启动 PostgreSQL 和 Redis。
- 本机通过 Poetry 启动 FastAPI、Celery worker、Celery beat。
- 本机通过 npm/Vite 启动前端。
- 脚本负责复制环境模板、同步 API Key、安装依赖、执行迁移、启动进程、记录 PID 和日志。

这个方案最贴近当前开发链路，也避免前端热更新、爬虫浏览器登录态、容器内 Python/Node 双栈编排带来的额外复杂度。

## 文件设计

- `scripts/dev-start.sh`：一键启动开发环境。
- `scripts/dev-stop.sh`：停止由启动脚本管理的本地进程。
- `docs/QUICKSTART.md`：clone 后快速运行文档。
- `README.md`：增加快速运行入口。
- `.gitignore`：忽略 `.vigor-dev/` 运行时目录。

## 启动流程

1. 检查 `docker`、`poetry`、`npm` 是否可用。
2. 创建 `.vigor-dev/logs` 和 `.vigor-dev/pids`。
3. 如果缺少 `vigor-server/.env`，从 `.env.example` 复制。
4. 如果缺少 `vigor-client/.env.local`，从 `.env.example` 复制，并将 `VITE_API_KEY` 改为后端 `API_KEY`。
5. 运行 `docker compose up -d postgres redis`。
6. 运行 `poetry install` 和 `npm install`。
7. 运行 `poetry run alembic upgrade head`。
8. 启动后端、Celery worker、Celery beat、前端。
9. 输出访问地址和日志路径。

## 停止流程

`scripts/dev-stop.sh` 读取 `.vigor-dev/pids/*.pid`，只停止脚本启动的本地进程。默认不停止 PostgreSQL 和 Redis，避免误关用户正在使用的数据服务；文档说明如需停止可执行 `docker compose stop postgres redis`。

## 错误处理

- 缺少基础工具时，脚本直接失败并提示安装。
- 端口被占用时，脚本提示 8000 或 3000 端口已有进程。
- 迁移失败时，脚本停止继续启动本地进程。
- 已有脚本启动的进程仍存活时，脚本复用并提示。

## 验证

- `bash -n scripts/dev-start.sh scripts/dev-stop.sh`
- `poetry run ruff check app tests`
- `npx vite build`
- 文档路径和命令均使用仓库根目录视角描述。
