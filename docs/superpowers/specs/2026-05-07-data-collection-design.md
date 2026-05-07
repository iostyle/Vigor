# Watcher 数据采集子系统设计文档

**日期**: 2026-05-07  
**版本**: 1.0  
**状态**: 待审核

## 1. 概述

本文档描述 Watcher 项目的数据采集子系统设计。该子系统负责从抖音平台爬取视频数据、生成智能摘要、管理数据更新,为下游的分析引擎和客户端提供数据源。

### 1.1 核心功能

- 根据关键词/领域/标签爬取抖音视频数据
- 支持多时间窗口(30日/15日/7日/3日/当日)和热度排序
- 智能摘要生成(视频摘要 + 评论摘要)
- 数据增量更新(优先级队列 + 手动触发)
- 管理后台(关键词管理、任务管理)
- 监控和告警(Prometheus + Grafana)

### 1.2 关键决策

- **爬取方式**: 混合方案(优先官方API,补充第三方服务/自建爬虫)
- **数据库**: PostgreSQL
- **智能摘要**: 豆包 API
- **更新策略**: 增量更新 + 优先级队列 + 手动触发
- **关键词管理**: 数据库 + 管理后台
- **任务调度**: Celery + Redis
- **技术栈**: Python + FastAPI
- **时间窗口**: 增量爬取 + 多维度索引
- **爬取数量**: 动态数量 + 热度阈值
- **评论处理**: 爬取热门评论 + 实时摘要
- **错误处理**: 重试 + 监控面板

## 2. 系统架构

### 2.1 整体架构

采用**单体架构 + 异步任务队列**方案,适合快速启动和中小规模部署。

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Application                      │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Admin API       │  │  Internal API    │                │
│  │  (管理后台接口)   │  │  (内部服务接口)   │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────┐
         │         Redis (消息队列 + 缓存)      │
         └────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Celery Worker Pool                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Crawler      │  │ Processor    │  │ Updater      │     │
│  │ Worker       │  │ Worker       │  │ Worker       │     │
│  │ (爬取任务)    │  │ (摘要生成)    │  │ (数据更新)    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────┐
         │         PostgreSQL (数据存储)        │
         └────────────────────────────────────┘
                          │
                          ▼
         ┌────────────────────────────────────┐
         │   Prometheus + Grafana (监控)       │
         └────────────────────────────────────┘
```

### 2.2 核心组件

**FastAPI Application**
- Admin API: 管理关键词、查看任务状态、手动触发更新
- Internal API: 供其他子系统(分析引擎、Client)调用,查询视频数据

**Celery Worker Pool**
- Crawler Worker: 执行爬取任务(调用抖音 API/第三方服务)
- Processor Worker: 调用豆包 API 生成视频摘要和评论摘要
- Updater Worker: 按优先级队列更新已存储视频的数据

**Redis**
- Celery 的消息队列(任务分发)
- 缓存层(热点数据、API 限流计数器)

**PostgreSQL**
- 存储所有数据(视频、评论、摘要、关键词配置)

**Prometheus + Grafana**
- 监控爬取成功率、任务队列长度、API 延迟等指标

### 2.3 架构选型理由

选择单体架构而非微服务的原因:
1. 快速启动 — 空仓库状态,单体架构可以最快验证整体流程
2. 成本可控 — 单机部署即可,后期流量增长再考虑拆分
3. 技术栈成熟 — FastAPI + Celery + PostgreSQL 是 Python 生态的黄金组合
4. 易于迭代 — 单体应用方便快速调整需求,不用跨服务协调
5. 符合 YAGNI 原则 — 不过度设计,等真正需要微服务时再重构

## 3. 数据库设计

### 3.1 核心表结构

**keywords (关键词配置表)**
```sql
CREATE TABLE keywords (
    id SERIAL PRIMARY KEY,
    keyword VARCHAR(255) NOT NULL,
    category VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    crawl_threshold INTEGER DEFAULT 1000,
    priority INTEGER DEFAULT 5,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**videos (视频数据表)**
```sql
CREATE TABLE videos (
    id SERIAL PRIMARY KEY,
    douyin_id VARCHAR(100) UNIQUE NOT NULL,
    keyword_id INTEGER REFERENCES keywords(id),
    title TEXT NOT NULL,
    author_name VARCHAR(255),
    author_id VARCHAR(100),
    cover_url TEXT,
    video_url TEXT,
    like_count INTEGER DEFAULT 0,
    comment_count INTEGER DEFAULT 0,
    share_count INTEGER DEFAULT 0,
    publish_time TIMESTAMP,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_at TIMESTAMP,
    heat_score FLOAT,
    summary TEXT,
    summary_generated_at TIMESTAMP
);
```

**comments (评论数据表)**
```sql
CREATE TABLE comments (
    id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES videos(id),
    douyin_comment_id VARCHAR(100) UNIQUE,
    author_name VARCHAR(255),
    content TEXT NOT NULL,
    like_count INTEGER DEFAULT 0,
    publish_time TIMESTAMP,
    crawled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**comment_summaries (评论摘要表)**
```sql
CREATE TABLE comment_summaries (
    id SERIAL PRIMARY KEY,
    video_id INTEGER REFERENCES videos(id),
    summary TEXT,
    top_keywords JSONB,
    sentiment VARCHAR(20),
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comment_count INTEGER
);
```

**crawl_tasks (爬取任务记录表)**
```sql
CREATE TABLE crawl_tasks (
    id SERIAL PRIMARY KEY,
    keyword_id INTEGER REFERENCES keywords(id),
    task_type VARCHAR(50),
    status VARCHAR(20),
    videos_crawled INTEGER DEFAULT 0,
    error_message TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);
```

### 3.2 索引设计

```sql
-- 按时间窗口 + 热度排序查询
CREATE INDEX idx_videos_publish_heat ON videos(publish_time DESC, heat_score DESC);

-- 按关键词查询
CREATE INDEX idx_videos_keyword ON videos(keyword_id);

-- 评论关联查询
CREATE INDEX idx_comments_video ON comments(video_id);

-- 全文搜索(标题和摘要)
CREATE INDEX idx_videos_title_search ON videos USING gin(to_tsvector('chinese', title));
CREATE INDEX idx_videos_summary_search ON videos USING gin(to_tsvector('chinese', summary));
```

### 3.3 数据库选型理由

选择 PostgreSQL 的原因:
- 支持复杂查询和事务
- 全文搜索能力(中文分词)
- JSONB 字段支持(存储评论关键词等非结构化数据)
- 成熟稳定,生态丰富
- 与 SQLAlchemy ORM 集成良好

## 4. 核心业务流程

### 4.1 关键词爬取流程

1. 用户在管理后台添加关键词
2. FastAPI 保存到 keywords 表
3. Celery Beat 触发定时任务(每小时执行一次)
4. Crawler Worker 读取 active 状态的关键词
5. 按优先级排序,依次执行爬取
6. 调用抖音 API/第三方服务
7. 按发布时间过滤(最近30日内)
8. 按热度排序,爬取到热度低于阈值时停止
9. 保存视频数据到 videos 表
10. 爬取每个视频的热门评论(Top 50)
11. 保存评论到 comments 表
12. 触发 Processor Worker 生成摘要

### 4.2 智能摘要生成流程

1. Processor Worker 接收任务(video_id)
2. 从数据库读取视频标题和评论内容
3. 调用豆包 API 生成摘要
4. 保存摘要到 videos.summary 和 comment_summaries 表
5. 记录生成时间戳

### 4.3 数据更新流程(优先级队列)

1. Updater Worker 定时执行(每小时)
2. 从 videos 表读取需要更新的视频,按 heat_score 排序
3. 过滤条件(根据热度决定更新频率):
   - heat_score > 10000: 每1小时更新
   - heat_score 1000-10000: 每6小时更新
   - heat_score < 1000: 每24小时更新
4. 批量调用抖音 API 获取最新数据
5. 更新 like_count, comment_count, share_count
6. 重新计算 heat_score
7. 如果评论数增长 > 20%,重新爬取评论并生成摘要
8. 更新 last_updated_at 时间戳

### 4.4 手动触发更新流程

1. 用户在管理后台点击"立即更新"
2. FastAPI 接收请求(video_id 或 keyword_id)
3. 创建高优先级 Celery 任务
4. Updater Worker 立即执行更新
5. 返回任务状态给前端

## 5. API 接口设计

### 5.1 Admin API (管理后台接口)

**关键词管理**
```
POST   /api/admin/keywords          # 创建关键词
GET    /api/admin/keywords          # 列出所有关键词
PUT    /api/admin/keywords/{id}     # 更新关键词配置
DELETE /api/admin/keywords/{id}     # 删除关键词(软删除)
```

**任务管理**
```
POST   /api/admin/tasks/crawl       # 手动触发爬取任务
POST   /api/admin/tasks/update      # 手动触发更新任务
GET    /api/admin/tasks             # 查看任务历史和状态
```

**视频管理**
```
GET    /api/admin/videos            # 列出视频(支持分页、筛选)
GET    /api/admin/videos/{id}       # 查看视频详情
POST   /api/admin/videos/{id}/update # 手动更新单个视频
```

### 5.2 Internal API (内部服务接口)

**数据查询(供分析引擎和Client调用)**
```
GET    /api/videos                  # 查询视频列表
  查询参数:
  - keyword_id: 按关键词筛选
  - time_window: 时间窗口(1d/3d/7d/15d/30d)
  - sort: 排序方式(heat_score/publish_time)
  - limit: 返回数量
  - offset: 分页偏移

GET    /api/videos/{id}             # 获取视频详情
GET    /api/videos/{id}/comments    # 获取视频评论
GET    /api/videos/{id}/summary     # 获取视频和评论摘要

GET    /api/stats/keywords          # 各关键词的视频数量统计
GET    /api/stats/trends            # 热度趋势数据
```

### 5.3 请求/响应示例

```json
GET /api/videos?keyword_id=1&time_window=7d&sort=heat_score&limit=10

Response:
{
  "total": 156,
  "data": [
    {
      "id": 1001,
      "douyin_id": "7234567890123456789",
      "title": "如何做出完美的红烧肉",
      "author_name": "美食达人小王",
      "like_count": 15600,
      "comment_count": 892,
      "heat_score": 18234.5,
      "publish_time": "2026-05-01T10:30:00Z",
      "summary": "视频展示了红烧肉的详细制作步骤...",
      "comment_summary": {
        "summary": "用户普遍关注火候控制和调料配比...",
        "sentiment": "positive",
        "top_keywords": ["火候", "调料", "软烂"]
      }
    }
  ]
}
```

## 6. 错误处理和监控

### 6.1 Celery 任务重试策略

```python
# 爬取任务重试配置
@celery_app.task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(RequestException, TimeoutError),
    retry_backoff=True,
    retry_backoff_max=600
)
def crawl_keyword_task(self, keyword_id):
    pass

# 摘要生成任务重试配置
@celery_app.task(
    bind=True,
    max_retries=5,
    default_retry_delay=30,
    autoretry_for=(APIError, RateLimitError)
)
def generate_summary_task(self, video_id):
    pass
```

### 6.2 监控指标(Prometheus)

**关键指标:**
- `crawl_tasks_total`: 爬取任务总数(按状态分类)
- `crawl_videos_total`: 爬取视频总数
- `crawl_duration_seconds`: 爬取任务耗时
- `api_requests_total`: API调用次数(按来源分类)
- `api_latency_seconds`: API响应延迟
- `celery_queue_length`: 任务队列长度(按队列分类)
- `douyin_api_errors_total`: 抖音API错误次数
- `douyin_api_rate_limit_hits`: 触发限流次数
- `summary_generation_total`: 摘要生成次数(成功/失败)
- `database_query_duration_seconds`: 数据库查询耗时

### 6.3 Grafana 监控面板

**面板1: 爬取概览**
- 今日爬取视频数量
- 今日爬取任务成功率
- 当前队列积压数量
- 平均爬取耗时

**面板2: API健康度**
- 抖音API调用成功率(最近1小时)
- 豆包API调用成功率(最近1小时)
- API响应延迟P50/P95/P99
- 限流触发次数

**面板3: 数据库性能**
- 数据库连接池使用率
- 慢查询数量(>1秒)
- 表大小增长趋势

**面板4: Worker状态**
- 活跃Worker数量
- 各队列任务分布
- 任务失败率(按类型)

## 7. 技术栈和部署

### 7.1 技术栈清单

**后端:**
- Python 3.11+
- FastAPI 0.100+ (Web框架)
- Celery 5.3+ (分布式任务队列)
- SQLAlchemy 2.0+ (ORM)
- Alembic (数据库迁移)
- Pydantic 2.0+ (数据验证)
- httpx (异步HTTP客户端)
- Redis 7.0+ (消息队列 + 缓存)
- PostgreSQL 15+ (数据库)

**监控:**
- Prometheus (指标采集)
- Grafana (可视化)
- prometheus-client (Python客户端)

**开发工具:**
- Poetry (依赖管理)
- pytest (测试框架)
- black + ruff (代码格式化和检查)
- pre-commit (Git钩子)

### 7.2 部署方案

**单机部署(推荐初期使用):**

使用 Docker Compose 部署所有服务,适合 4核8G 服务器。

**项目目录结构:**
```
watcher-server/
├── app/
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置管理
│   ├── celery_app.py        # Celery配置
│   ├── database.py          # 数据库连接
│   ├── models/              # SQLAlchemy模型
│   ├── schemas/             # Pydantic schemas
│   ├── api/                 # API路由
│   │   ├── admin/
│   │   └── internal/
│   ├── tasks/               # Celery任务
│   │   ├── crawler.py
│   │   ├── processor.py
│   │   └── updater.py
│   ├── services/            # 业务逻辑
│   │   ├── douyin_client.py
│   │   ├── doubao_client.py
│   │   └── heat_calculator.py
│   └── utils/
│       ├── metrics.py       # Prometheus指标
│       └── retry.py
├── alembic/                 # 数据库迁移
├── tests/
├── docker-compose.yml
├── Dockerfile
├── pyproject.toml
└── README.md
```

## 8. 测试策略

### 8.1 单元测试

测试覆盖范围:
- 数据模型(models/)
- 业务逻辑(services/)
- 工具函数(utils/)
- API schemas验证

### 8.2 集成测试

测试覆盖范围:
- API端点(FastAPI routes)
- Celery任务执行
- 数据库操作
- 外部API调用(使用Mock)

### 8.3 测试环境配置

使用 pytest + Docker 测试数据库,配置代码覆盖率报告。

## 9. 安全和性能考虑

### 9.1 安全措施

1. **API认证** — Admin API使用JWT token,Internal API使用API Key
2. **敏感信息管理** — API密钥存储在环境变量
3. **SQL注入防护** — 使用SQLAlchemy ORM参数化查询
4. **限流保护** — Redis实现API限流(每IP每分钟100次)
5. **数据脱敏** — 日志中不记录完整API密钥

### 9.2 性能优化

1. **数据库连接池** — pool_size=20, max_overflow=10
2. **查询优化** — 使用索引,避免N+1查询,分页查询
3. **缓存策略** — 热点数据缓存到Redis,TTL 5分钟
4. **异步处理** — FastAPI使用async/await
5. **批量操作** — 数据库批量插入/更新
6. **API限流** — 对外部API调用进行限流

## 10. 后续演进路径

当流量增长到单机无法支撑时,可以平滑演进到微服务架构:

1. 先把 Crawler 逻辑抽成独立 Worker 池
2. 再把 Processing 逻辑拆成独立服务
3. 最后引入 API Gateway 和服务网格

---

**文档结束**
