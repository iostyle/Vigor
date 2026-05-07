# Vigor 数据采集子系统实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建 Vigor 数据采集子系统,实现抖音视频爬取、智能摘要生成、数据更新管理和监控功能

**Architecture:** 单体架构 + 异步任务队列,FastAPI 提供 API 服务,Celery Worker 处理爬取和数据处理任务,PostgreSQL 存储数据,Redis 作为消息队列和缓存

**Tech Stack:** Python 3.11+, FastAPI, Celery, SQLAlchemy, PostgreSQL, Redis, Alembic, pytest, Prometheus

---

## 文件结构规划

本实现将创建以下文件结构:

```
vigor-server/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI 应用入口
│   ├── config.py                  # 配置管理
│   ├── database.py                # 数据库连接
│   ├── celery_app.py              # Celery 配置
│   ├── models/
│   │   ├── __init__.py
│   │   ├── keyword.py             # 关键词模型
│   │   ├── video.py               # 视频模型
│   │   ├── comment.py             # 评论模型
│   │   └── task.py                # 任务记录模型
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── keyword.py             # 关键词 schema
│   │   ├── video.py               # 视频 schema
│   │   └── task.py                # 任务 schema
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py                # 依赖注入
│   │   ├── admin/
│   │   │   ├── __init__.py
│   │   │   ├── keywords.py        # 关键词管理 API
│   │   │   ├── tasks.py           # 任务管理 API
│   │   │   └── videos.py          # 视频管理 API
│   │   └── internal/
│   │       ├── __init__.py
│   │       ├── videos.py          # 视频查询 API
│   │       └── stats.py           # 统计 API
│   ├── tasks/
│   │   ├── __init__.py
│   │   ├── crawler.py             # 爬取任务
│   │   ├── processor.py           # 摘要生成任务
│   │   └── updater.py             # 数据更新任务
│   ├── services/
│   │   ├── __init__.py
│   │   ├── douyin_client.py       # 抖音 API 客户端
│   │   ├── doubao_client.py       # 豆包 API 客户端
│   │   └── heat_calculator.py     # 热度计算
│   └── utils/
│       ├── __init__.py
│       ├── metrics.py             # Prometheus 指标
│       └── retry.py               # 重试逻辑
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_models.py
│   ├── test_api_keywords.py
│   └── test_tasks_crawler.py
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
├── pytest.ini
├── .env.example
└── README.md
```

---

## Task 1: 项目初始化和依赖配置

**Files:**
- Create: `vigor-server/pyproject.toml`
- Create: `vigor-server/.env.example`
- Create: `vigor-server/README.md`

- [ ] **Step 1: 创建 vigor-server 目录**

```bash
mkdir -p vigor-server
cd vigor-server
```

- [ ] **Step 2: 初始化 Poetry 项目**

```bash
poetry init --name vigor-server --python "^3.11" --no-interaction
```

- [ ] **Step 3: 添加核心依赖**

```bash
poetry add fastapi uvicorn[standard] sqlalchemy alembic psycopg2-binary pydantic-settings celery redis httpx prometheus-client
```

- [ ] **Step 4: 添加开发依赖**

```bash
poetry add --group dev pytest pytest-asyncio pytest-cov black ruff pre-commit
```

- [ ] **Step 5: 创建 .env.example 文件**

创建文件 `vigor-server/.env.example`,内容包含数据库、Redis、Celery、外部 API 和安全配置的环境变量模板。

- [ ] **Step 6: 创建 README.md**

创建文件 `vigor-server/README.md`,包含项目介绍、技术栈、快速开始指南和开发命令。

- [ ] **Step 7: 提交**

```bash
git add vigor-server/
git commit -m "feat: initialize vigor-server project with Poetry"
```

---

## Task 2: 数据库配置和连接

**Files:**
- Create: `vigor-server/app/__init__.py`
- Create: `vigor-server/app/config.py`
- Create: `vigor-server/app/database.py`
- Create: `vigor-server/tests/__init__.py`
- Create: `vigor-server/tests/conftest.py`

- [ ] **Step 1: 编写测试 - 配置加载**

```python
# tests/test_config.py
from app.config import Settings

def test_settings_loads_from_env():
    settings = Settings()
    assert settings.DATABASE_URL is not None
    assert settings.REDIS_URL is not None
```

- [ ] **Step 2: 运行测试验证失败**

```bash
cd vigor-server
poetry run pytest tests/test_config.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.config'"

- [ ] **Step 3: 实现配置管理**

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    DOUYIN_API_KEY: str
    DOUBAO_API_KEY: str
    SECRET_KEY: str
    API_KEY: str
    ENVIRONMENT: str = "development"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()
```

- [ ] **Step 4: 创建空的 __init__.py**

```python
# app/__init__.py
# Empty file to make app a package
```

- [ ] **Step 5: 运行测试验证通过**

```bash
poetry run pytest tests/test_config.py -v
```

Expected: PASS

- [ ] **Step 6: 编写测试 - 数据库连接**

```python
# tests/test_database.py
from app.database import get_db, engine
from sqlalchemy import text

def test_database_connection():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        assert result.scalar() == 1
```

- [ ] **Step 7: 运行测试验证失败**

```bash
poetry run pytest tests/test_database.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.database'"

- [ ] **Step 8: 实现数据库连接**

```python
# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 9: 运行测试验证通过**

```bash
poetry run pytest tests/test_database.py -v
```

Expected: PASS (需要 PostgreSQL 运行)

- [ ] **Step 10: 提交**

```bash
git add app/ tests/
git commit -m "feat: add database configuration and connection"
```

---

## Task 3: 数据模型定义

**Files:**
- Create: `vigor-server/app/models/__init__.py`
- Create: `vigor-server/app/models/keyword.py`
- Create: `vigor-server/app/models/video.py`
- Create: `vigor-server/app/models/comment.py`
- Create: `vigor-server/app/models/task.py`
- Create: `vigor-server/tests/test_models.py`

- [ ] **Step 1: 编写测试 - Keyword 模型**

```python
# tests/test_models.py
from app.models.keyword import Keyword
from app.database import SessionLocal

def test_keyword_model_creation():
    db = SessionLocal()
    keyword = Keyword(
        keyword="美食",
        category="生活",
        status="active",
        crawl_threshold=1000,
        priority=5
    )
    db.add(keyword)
    db.commit()
    db.refresh(keyword)
    
    assert keyword.id is not None
    assert keyword.keyword == "美食"
    assert keyword.status == "active"
    
    db.delete(keyword)
    db.commit()
    db.close()
```

- [ ] **Step 2: 运行测试验证失败**

```bash
poetry run pytest tests/test_models.py::test_keyword_model_creation -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'app.models.keyword'"

- [ ] **Step 3: 实现 Keyword 模型**

```python
# app/models/keyword.py
from sqlalchemy import Column, Integer, String, TIMESTAMP
from sqlalchemy.sql import func
from app.database import Base

class Keyword(Base):
    __tablename__ = "keywords"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword = Column(String(255), nullable=False)
    category = Column(String(100))
    status = Column(String(20), default="active")
    crawl_threshold = Column(Integer, default=1000)
    priority = Column(Integer, default=5)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
```

- [ ] **Step 4: 创建 models __init__.py**

```python
# app/models/__init__.py
from app.models.keyword import Keyword
from app.models.video import Video
from app.models.comment import Comment
from app.models.task import CrawlTask

__all__ = ["Keyword", "Video", "Comment", "CrawlTask"]
```

- [ ] **Step 5: 运行测试验证通过**

```bash
poetry run pytest tests/test_models.py::test_keyword_model_creation -v
```

Expected: PASS

- [ ] **Step 6: 实现 Video 模型**

```python
# app/models/video.py
from sqlalchemy import Column, Integer, String, Text, Float, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True, index=True)
    douyin_id = Column(String(100), unique=True, nullable=False, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    title = Column(Text, nullable=False)
    author_name = Column(String(255))
    author_id = Column(String(100))
    cover_url = Column(Text)
    video_url = Column(Text)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    share_count = Column(Integer, default=0)
    publish_time = Column(TIMESTAMP)
    crawled_at = Column(TIMESTAMP, server_default=func.now())
    last_updated_at = Column(TIMESTAMP)
    heat_score = Column(Float)
    summary = Column(Text)
    summary_generated_at = Column(TIMESTAMP)
    
    keyword = relationship("Keyword", backref="videos")
    comments = relationship("Comment", back_populates="video", cascade="all, delete-orphan")
```

- [ ] **Step 7: 实现 Comment 模型**

```python
# app/models/comment.py
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base

class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), index=True)
    douyin_comment_id = Column(String(100), unique=True)
    author_name = Column(String(255))
    content = Column(Text, nullable=False)
    like_count = Column(Integer, default=0)
    publish_time = Column(TIMESTAMP)
    crawled_at = Column(TIMESTAMP, server_default=func.now())
    
    video = relationship("Video", back_populates="comments")

class CommentSummary(Base):
    __tablename__ = "comment_summaries"
    
    id = Column(Integer, primary_key=True, index=True)
    video_id = Column(Integer, ForeignKey("videos.id"), unique=True)
    summary = Column(Text)
    top_keywords = Column(Text)  # JSON string
    sentiment = Column(String(20))
    generated_at = Column(TIMESTAMP, server_default=func.now())
    comment_count = Column(Integer)
```

- [ ] **Step 8: 实现 CrawlTask 模型**

```python
# app/models/task.py
from sqlalchemy import Column, Integer, String, Text, TIMESTAMP, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class CrawlTask(Base):
    __tablename__ = "crawl_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    keyword_id = Column(Integer, ForeignKey("keywords.id"))
    task_type = Column(String(50))
    status = Column(String(20))
    videos_crawled = Column(Integer, default=0)
    error_message = Column(Text)
    started_at = Column(TIMESTAMP)
    completed_at = Column(TIMESTAMP)
```

- [ ] **Step 9: 提交**

```bash
git add app/models/ tests/test_models.py
git commit -m "feat: add database models for keywords, videos, comments, and tasks"
```

---

## Task 4: 数据库迁移配置

**Files:**
- Create: `vigor-server/alembic.ini`
- Create: `vigor-server/alembic/env.py`
- Create: `vigor-server/alembic/script.py.mako`
- Create: `vigor-server/alembic/versions/001_initial_schema.py`

- [ ] **Step 1: 初始化 Alembic**

```bash
cd vigor-server
poetry run alembic init alembic
```

- [ ] **Step 2: 配置 Alembic env.py**

修改 `alembic/env.py`,导入模型并配置数据库连接:

```python
# alembic/env.py (关键部分)
from app.config import settings
from app.database import Base
from app.models import Keyword, Video, Comment, CrawlTask

target_metadata = Base.metadata

def get_url():
    return settings.DATABASE_URL
```

- [ ] **Step 3: 创建初始迁移**

```bash
poetry run alembic revision --autogenerate -m "initial schema"
```

- [ ] **Step 4: 运行迁移**

```bash
poetry run alembic upgrade head
```

Expected: 数据库表创建成功

- [ ] **Step 5: 验证表创建**

```bash
poetry run python -c "from app.database import engine; from sqlalchemy import inspect; print(inspect(engine).get_table_names())"
```

Expected: 输出包含 keywords, videos, comments, comment_summaries, crawl_tasks

- [ ] **Step 6: 提交**

```bash
git add alembic/ alembic.ini
git commit -m "feat: add Alembic database migration configuration"
```

---

## 实现计划总结

本实现计划包含 **4 个核心任务**,涵盖了 Vigor 数据采集子系统的基础架构:

### 已完成的任务规划:

1. **Task 1: 项目初始化和依赖配置** - 设置 Poetry 项目,安装依赖,创建配置文件
2. **Task 2: 数据库配置和连接** - 实现配置管理和数据库连接
3. **Task 3: 数据模型定义** - 定义 Keyword, Video, Comment, CrawlTask 模型
4. **Task 4: 数据库迁移配置** - 配置 Alembic 并创建初始迁移

### 后续任务概要(需要继续规划):

5. **Pydantic Schemas** - 定义 API 请求/响应模型
6. **Admin API - 关键词管理** - 实现 CRUD 接口
7. **Admin API - 任务管理** - 实现任务触发和查询接口
8. **Admin API - 视频管理** - 实现视频查询和更新接口
9. **Internal API - 视频查询** - 实现视频列表和详情接口
10. **Internal API - 统计** - 实现统计接口
11. **Celery 配置** - 配置 Celery 应用和队列
12. **Celery 任务 - 爬取** - 实现爬取任务
13. **Celery 任务 - 处理** - 实现摘要生成任务
14. **Celery 任务 - 更新** - 实现数据更新任务
15. **抖音客户端** - 实现抖音 API 客户端
16. **豆包客户端** - 实现豆包 API 客户端
17. **热度计算** - 实现热度分数计算逻辑
18. **Docker 配置** - 创建 Dockerfile 和 docker-compose.yml
19. **Prometheus 监控** - 配置监控指标
20. **FastAPI 主应用** - 整合所有模块,启动应用

---

## 执行建议

**推荐方式: Subagent-Driven Development**

使用 `superpowers:subagent-driven-development` skill 执行此计划:
- 每个任务由独立的 subagent 执行
- 任务完成后进行两阶段审查
- 可以并行执行独立任务
- 更快的迭代速度

**替代方式: Inline Execution**

使用 `superpowers:executing-plans` skill 在当前会话执行:
- 批量执行任务
- 在检查点进行审查
- 适合顺序依赖的任务

---

## 下一步

当前计划已保存到 `docs/superpowers/plans/2026-05-07-data-collection-implementation.md`。

**你希望:**

A. 我继续编写完整的 20 个任务(包含所有详细步骤)
B. 使用 subagent-driven-development 开始执行 Task 1-4
C. 使用 executing-plans 在当前会话执行 Task 1-4
D. 其他建议

请选择 A、B、C 或 D。
