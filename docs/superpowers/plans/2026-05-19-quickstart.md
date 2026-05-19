# Vigor Quickstart Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 新增快速运行文档和一键启动/停止脚本，让新设备 clone 后可以快速启动本地开发环境。

**Architecture:** 使用 Shell 脚本编排现有开发链路：Docker 负责 PostgreSQL 和 Redis，本机 Poetry 负责后端与 Celery，本机 npm/Vite 负责前端。脚本只管理自身启动的进程，运行时状态放在 `.vigor-dev/`。

**Tech Stack:** Bash、Docker Compose、Poetry、Alembic、Celery、Vite、Markdown。

---

### Task 1: 编写运行时目录忽略规则

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: 添加 `.vigor-dev/` 忽略规则**

```gitignore
# Vigor local dev runtime
.vigor-dev/
```

- [ ] **Step 2: 检查状态**

Run: `git status --short`

Expected: `.gitignore` 显示为修改。

### Task 2: 实现启动脚本

**Files:**
- Create: `scripts/dev-start.sh`

- [ ] **Step 1: 创建 Bash 脚本**

脚本需要包含：

```bash
#!/usr/bin/env bash
set -euo pipefail
```

核心函数：

- `require_command`：检查 `docker`、`poetry`、`npm`。
- `compose_cmd`：兼容 `docker compose` 和 `docker-compose`。
- `copy_env_files`：复制后端和前端环境文件，并同步 API Key。
- `ensure_port_free`：检查 8000 和 3000。
- `start_process`：用 `nohup` 启动服务，写入 PID。
- `wait_for_http`：等待后端健康。

- [ ] **Step 2: 验证语法**

Run: `bash -n scripts/dev-start.sh`

Expected: exit code 0。

### Task 3: 实现停止脚本

**Files:**
- Create: `scripts/dev-stop.sh`

- [ ] **Step 1: 创建 Bash 脚本**

脚本读取 `.vigor-dev/pids/*.pid`，对仍存活的 PID 发送 `TERM`，等待后必要时发送 `KILL`，最后删除 PID 文件。

- [ ] **Step 2: 验证语法**

Run: `bash -n scripts/dev-stop.sh`

Expected: exit code 0。

### Task 4: 编写快速运行文档

**Files:**
- Create: `docs/QUICKSTART.md`
- Modify: `README.md`

- [ ] **Step 1: 编写 `docs/QUICKSTART.md`**

内容包括：

- 前置依赖。
- clone 后一键启动命令。
- 访问地址。
- 环境变量说明。
- 日志和停止命令。
- 常见问题。

- [ ] **Step 2: 更新 `README.md`**

在开头增加快速启动入口：

```markdown
## 快速运行

新设备 clone 后可参考 [快速运行文档](docs/QUICKSTART.md)。
```

### Task 5: 验证

**Files:**
- Test: `scripts/dev-start.sh`
- Test: `scripts/dev-stop.sh`
- Test: `docs/QUICKSTART.md`

- [ ] **Step 1: Shell 语法检查**

Run: `bash -n scripts/dev-start.sh scripts/dev-stop.sh`

Expected: exit code 0。

- [ ] **Step 2: 后端 lint**

Run: `cd vigor-server && poetry run ruff check app tests`

Expected: `All checks passed!`

- [ ] **Step 3: 前端构建**

Run: `cd vigor-client && npx vite build`

Expected: `built` 成功。
