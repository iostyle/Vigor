# Scheduled Task Monitor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在定时任务管理页增加实时监控模块，展示调度器心跳、触发情况、任务来源和异常诊断。

**Architecture:** 后端新增调度器扫描记录表和监控聚合接口；调度器每次扫描写入记录；前端通过轮询接口展示监控卡片和最近记录。监控依据数据库状态，不依赖 Celery inspect。

**Tech Stack:** FastAPI、SQLAlchemy、Alembic、Pydantic、Vue 3、Naive UI、TypeScript。

---

### Task 1: 调度器扫描记录模型

**Files:**
- Create: `vigor-server/app/models/scheduled_task_run.py`
- Modify: `vigor-server/app/models/__init__.py`
- Modify: `vigor-server/alembic/env.py`
- Create: `vigor-server/alembic/versions/d0e1f2a3b4c5_add_scheduled_task_runs.py`

- [x] 新增 `ScheduledTaskRun` 模型，字段包含 `status`、`started_at`、`finished_at`、`due_count`、`dispatched_count`、`failed_count`、`triggered_task_ids`、`error_message`。
- [x] Alembic 创建 `scheduled_task_runs` 表和 `started_at` 索引。

### Task 2: 调度器写入扫描记录

**Files:**
- Modify: `vigor-server/app/services/scheduled_tasks.py`
- Modify: `vigor-server/tests/test_services_scheduled_tasks.py`

- [x] `run_due_scheduled_tasks` 开始时创建 run record。
- [x] 每个 due task 成功/失败后更新统计。
- [x] 结束时写入 `finished_at`、`status`、`triggered_task_ids`。
- [x] 测试 run record 写入和来源参数。

### Task 3: 监控 API

**Files:**
- Modify: `vigor-server/app/schemas/scheduled_task.py`
- Modify: `vigor-server/app/api/admin/scheduled_tasks.py`
- Modify: `vigor-server/tests/test_api_scheduled_tasks.py`

- [x] 新增 monitor response schemas。
- [x] 新增 `GET /api/admin/scheduled-tasks/monitor`。
- [x] 聚合任务总览、最近 24 小时任务状态、最近任务、最近扫描记录。

### Task 4: 前端监控面板

**Files:**
- Modify: `vigor-client/src/api/scheduledTask.ts`
- Modify: `vigor-client/src/views/admin/ScheduledTasksPage.vue`

- [x] 增加 monitor API 类型和请求方法。
- [x] 页面顶部展示健康状态、调度器心跳、任务统计、最近扫描和最近任务。
- [x] 每 5 秒轮询，卸载时清理 timer。

### Task 5: 验证

**Files:**
- Test: `vigor-server/tests/test_api_scheduled_tasks.py`
- Test: `vigor-server/tests/test_services_scheduled_tasks.py`
- Test: `vigor-client/src/views/admin/ScheduledTasksPage.vue`

- [x] Run: `poetry run pytest tests/test_api_scheduled_tasks.py tests/test_services_scheduled_tasks.py tests/test_celery_config.py`
- [x] Run: `poetry run ruff check app tests`
- [x] Run: `npx vite build`
