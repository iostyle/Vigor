# Vigor 快速运行

这份文档面向新设备。clone 仓库后，按下面步骤可以快速启动本地开发环境。

## 前置依赖

请先安装：

- Docker Desktop，提供 PostgreSQL 和 Redis。
- Python 3.11。
- Poetry。
- Node.js 18+ 和 npm。

可用下面命令检查：

```bash
docker --version
poetry --version
node --version
npm --version
```

## 一键启动

在仓库根目录执行：

```bash
chmod +x scripts/dev-start.sh scripts/dev-stop.sh
./scripts/dev-start.sh
```

脚本会自动完成：

- 创建 `vigor-server/.env`。
- 创建 `vigor-client/.env.local`，并同步后端 API Key。
- 启动 PostgreSQL 和 Redis。
- 安装后端和前端依赖。
- 执行数据库迁移。
- 启动 FastAPI、Celery worker、Celery beat 和 Vite。

启动完成后访问：

- 客户端和后台：http://localhost:3000
- API 文档：http://localhost:8000/docs

## 停止服务

停止脚本启动的本地进程：

```bash
./scripts/dev-stop.sh
```

## 日常开发重启

修改后端、Celery 任务或前端配置后，如果热更新没有生效，可以使用重启脚本：

```bash
chmod +x scripts/dev-restart.sh scripts/dev-status.sh

# 重启全部开发进程
./scripts/dev-restart.sh

# 只重启后端 API
./scripts/dev-restart.sh api

# 只重启前端 Vite
./scripts/dev-restart.sh client

# 只重启 Celery worker
./scripts/dev-restart.sh worker

# 只重启 Celery beat
./scripts/dev-restart.sh beat
```

查看脚本管理的进程和端口状态：

```bash
./scripts/dev-status.sh
```

定时任务监控如果显示“扫描异常”，优先检查：

```bash
./scripts/dev-status.sh
tail -n 120 .vigor-dev/logs/celery-worker.log
tail -n 120 .vigor-dev/logs/celery-beat.log
```

如果日志中出现 `Received unregistered task of type 'app.tasks.scheduler.run_scheduled_tasks'`，说明有旧 Celery worker 仍在运行。先停止旧进程，再执行：

```bash
./scripts/dev-restart.sh worker
./scripts/dev-restart.sh beat
```

默认不会停止 PostgreSQL 和 Redis，避免误关数据库。需要停止基础服务时执行：

```bash
cd vigor-server
docker compose stop postgres redis
```

需要清空数据库数据时再执行：

```bash
cd vigor-server
docker compose down -v
```

## 日志和进程文件

脚本运行时目录在 `.vigor-dev/`：

- `.vigor-dev/logs/api.log`
- `.vigor-dev/logs/celery-worker.log`
- `.vigor-dev/logs/celery-beat.log`
- `.vigor-dev/logs/client.log`
- `.vigor-dev/pids/*.pid`

`.vigor-dev/` 已加入 `.gitignore`，不会提交到仓库。

## 环境变量

后端配置文件：`vigor-server/.env`

常用字段：

- `API_KEY`：前后端 API 鉴权 key，脚本会同步到前端。
- `DOUYIN_MOCK_MODE`：默认 `true`，新设备可先用 mock 模式跑通。
- `DOUBAO_MOCK_MODE`：默认 `true`，新设备可先不配置真实大模型 key。
- `BILIBILI_MOCK_MODE`：默认 `true`，新设备可先不配置 B 站登录态。
- `AUTO_GENERATE_SUMMARY_AFTER_CRAWL`：默认 `false`，爬取后不自动生成评论摘要。

前端配置文件：`vigor-client/.env.local`

常用字段：

- `VITE_API_BASE_URL=http://localhost:8000`
- `VITE_API_KEY=<与后端 API_KEY 一致>`

修改环境变量后，重新运行：

```bash
./scripts/dev-restart.sh
```

## 常见问题

### 端口被占用

默认使用：

- 后端：`8000`
- 前端：`3000`
- PostgreSQL：`5432`
- Redis：`6379`

如果 8000 或 3000 被占用，可以临时指定端口：

```bash
API_PORT=8010 CLIENT_PORT=3010 ./scripts/dev-start.sh
```

### Docker 没有启动

如果脚本提示无法连接 Docker，请先启动 Docker Desktop，再重新运行脚本。

### 数据库迁移失败

先确认 PostgreSQL 已启动：

```bash
cd vigor-server
docker compose ps postgres
```

再重新执行：

```bash
poetry run alembic upgrade head
```

### B 站或真实爬虫需要登录态

快速启动默认只保证本地服务链路跑通。真实平台爬取可能需要登录态、浏览器数据目录或外部平台账号配置，请在跑通基础服务后再单独配置。

### 评论摘要没有真实大模型结果

默认 `DOUBAO_MOCK_MODE=true`。如果要调用真实大模型，需要在 `vigor-server/.env` 中配置：

```bash
DOUBAO_MOCK_MODE=false
DOUBAO_API_KEY=<真实 key>
DOUBAO_ENDPOINT_ID=<真实 endpoint id>
```

### 只启动后端基础服务

```bash
cd vigor-server
docker compose up -d postgres redis
poetry install
poetry run alembic upgrade head
poetry run uvicorn app.main:app --reload
```

### 只启动前端

```bash
cd vigor-client
npm install
npm run dev
```
