# Vigor Server

Vigor 数据采集子系统 - 基于 FastAPI 的抖音视频数据采集和分析服务

## 技术栈

- **Web 框架**: FastAPI + Uvicorn
- **数据库**: PostgreSQL + SQLAlchemy + Alembic
- **任务队列**: Celery + Redis
- **HTTP 客户端**: httpx
- **监控**: Prometheus
- **测试**: pytest + pytest-asyncio
- **代码质量**: black + ruff + pre-commit

## 快速开始

### 1. 安装依赖

```bash
poetry install
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件,填入实际的配置信息
```

### 3. 启动数据库和 Redis

```bash
docker-compose up -d postgres redis
```

### 4. 运行数据库迁移

```bash
poetry run alembic upgrade head
```

### 5. 启动开发服务器

```bash
poetry run uvicorn app.main:app --reload
```

API 文档: http://localhost:8000/docs

## 开发命令

### 运行测试

```bash
# 运行所有测试
poetry run pytest

# 运行测试并生成覆盖率报告
poetry run pytest --cov=app --cov-report=html
```

### 代码格式化和检查

```bash
# 格式化代码
poetry run black app/ tests/

# 代码检查
poetry run ruff check app/ tests/

# 自动修复
poetry run ruff check --fix app/ tests/
```

### 数据库迁移

```bash
# 创建新的迁移
poetry run alembic revision --autogenerate -m "description"

# 应用迁移
poetry run alembic upgrade head

# 回滚迁移
poetry run alembic downgrade -1
```

### 启动 Celery Worker

```bash
poetry run celery -A app.celery_app worker --loglevel=info
```

## 项目结构

```
vigor-server/
├── app/                    # 应用代码
│   ├── main.py            # FastAPI 应用入口
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库连接
│   ├── celery_app.py      # Celery 配置
│   ├── models/            # 数据模型
│   ├── schemas/           # Pydantic schemas
│   ├── api/               # API 路由
│   ├── tasks/             # Celery 任务
│   ├── services/          # 外部服务客户端
│   └── utils/             # 工具函数
├── alembic/               # 数据库迁移
├── tests/                 # 测试代码
├── docker-compose.yml     # Docker 配置
├── pyproject.toml         # Poetry 配置
└── .env.example           # 环境变量模板
```

## License

MIT
