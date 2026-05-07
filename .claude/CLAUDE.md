# Vigor 项目 Claude 配置

## 项目概述

Vigor 是一个基于抖音数据的领域分析平台,分为 Server(数据采集、分析引擎)和 Client(Vue 3 Web 应用)两部分。

- **项目仓库**: git@github.com:iostyle/Vigor.git
- **项目目录**: `/Users/iostyle/WorkSpace/AIWorkSpace/Vigor`
- **文档目录**: `docs/superpowers/` (specs/ 和 plans/)

## 工作流程规范

### 1. 分析和设计
- **必须使用** `/superpowers:brainstorming` 进行项目分析和设计
- 每个新功能或子系统都需要经过头脑风暴流程
- 设计文档保存到 `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`

### 2. 实现计划
- **必须使用** `/superpowers:writing-plans` 编写详细的实现计划
- 实现计划保存到 `docs/superpowers/plans/YYYY-MM-DD-<feature>.md`
- 遵循 TDD 原则,每个任务分解为可执行的小步骤

### 3. 开发模式
- **严格使用 AgentTeam 模式进行开发**,团队成员可相互实时沟通讨论
- 使用 TeamCreate 创建团队,Agent 派发成员
- 任务通过 TaskCreate / TaskUpdate 管理
- 成员间通过 SendMessage 沟通
- 所有Claude配置存储在当前项目目录中

### 4. UI 设计
- UI 借鉴 **Apple 风格**:简洁、优雅、注重留白
- 使用 Naive UI 组件库(Vue 3)
- 支持浅色/深色双主题
- 流畅的动画和过渡效果
- 响应式设计,兼容桌面端和移动端

## 团队角色配置

所有角色定义位于 `.claude/agents/` 目录下,以下是预设角色:

### 研发部门角色

| 角色文件 | 角色名称 | 职责 |
|---------|---------|------|
| `manager.md` | 管理者 | 任务分配、进度跟踪、团队协调 |
| `architect.md` | 架构师 | 技术选型、架构设计、技术决策 |
| `backend-dev.md` | 后端开发工程师 | API 开发、业务逻辑、数据库操作 |
| `frontend-dev.md` | 前端开发工程师 | Vue 3 开发、UI 实现、接口对接 |
| `database-engineer.md` | 数据库工程师 | 数据库设计、数据模型、查询优化 |
| `devops-engineer.md` | DevOps 工程师 | 部署、容器化、CI/CD、监控 |
| `ui-designer.md` | UI 设计师 | 界面设计、交互设计(Apple 风格) |
| `qa-engineer.md` | 软件测试工程师 | 测试用例、自动化测试、质量保证 |

### 领域专家

领域专家根据项目需要动态创建:

- `domain-expert-template.md` - 领域专家模板
- 根据需要创建具体的领域专家(如美食、科技、教育等)

### 如何使用角色

1. **查找现有角色**:查看 `.claude/agents/` 目录
2. **创建新角色**:复制 `domain-expert-template.md` 并修改
3. **派发成员**:使用 Agent 工具 + team_name + name 参数
4. **参考示例**:查看 `team-config.md` 了解当前活跃团队

## 当前活跃团队

- **vigor-dev-team**: Vigor 数据采集子系统开发团队
  - 详情见 `.claude/agents/team-config.md`
  - **团队配置**: `.claude/teams/vigor-dev-team/config.json`
  - **任务状态**: `.claude/tasks/vigor-dev-team/*.json`
  - **消息收件箱**: `.claude/teams/vigor-dev-team/inboxes/`

### 存储位置

所有 Claude 配置与运行时数据均存储在**当前项目目录** `.claude/` 下。Claude Code 默认读写 `~/.claude/teams/<team-name>` 和 `~/.claude/tasks/<team-name>`,本项目通过**符号链接**把这两个系统路径指向项目目录:

```
~/.claude/teams/vigor-dev-team  →  .claude/teams/vigor-dev-team
~/.claude/tasks/vigor-dev-team  →  .claude/tasks/vigor-dev-team
```

这样读写仍然发生在项目目录,能被 git 追踪、随项目迁移。

### 新环境部署

克隆仓库到新机器后,执行以下命令重建符号链接:

```bash
cd <project-dir>
mkdir -p ~/.claude/teams ~/.claude/tasks
ln -sfn "$PWD/.claude/teams/vigor-dev-team" ~/.claude/teams/vigor-dev-team
ln -sfn "$PWD/.claude/tasks/vigor-dev-team" ~/.claude/tasks/vigor-dev-team
```

详见 `.claude/teams/README.md`

## 文档结构

```
Vigor/
├── .claude/
│   ├── CLAUDE.md              # 项目 Claude 配置(本文件)
│   ├── agents/                # 团队角色定义
│   │   ├── manager.md
│   │   ├── architect.md
│   │   ├── backend-dev.md
│   │   ├── frontend-dev.md
│   │   ├── database-engineer.md
│   │   ├── devops-engineer.md
│   │   ├── ui-designer.md
│   │   ├── qa-engineer.md
│   │   ├── domain-expert-template.md
│   │   └── team-config.md     # 当前团队配置
│   ├── teams/                 # 团队配置(权威位置,~/.claude 通过 symlink 指向此)
│   │   ├── README.md          # 说明文档
│   │   └── vigor-dev-team/
│   │       ├── config.json
│   │       └── inboxes/       # 成员消息收件箱
│   └── tasks/                 # 任务状态(权威位置,~/.claude 通过 symlink 指向此)
│       └── vigor-dev-team/
│           └── *.json
├── docs/
│   └── superpowers/
│       ├── specs/             # 设计文档
│       └── plans/             # 实现计划
├── vigor-server/              # 服务端代码
└── vigor-client/              # 客户端代码(待创建)
```

## 关键约定

1. **所有文档和注释使用中文**
2. **代码注释尽量精简**,只说明 Why 不说 What
3. **严格遵循 TDD**,先写测试再写实现
4. **频繁提交代码**,每个小任务完成后就提交
5. **使用 git commit 规范**:feat/fix/docs/refactor/test
6. **不创建临时的 .md 文档**,除非用户明确要求

## 常用命令参考

### 项目管理
```bash
# 启动后端服务
cd vigor-server && poetry run uvicorn app.main:app --reload

# 启动 Docker 服务
docker-compose up -d

# 运行测试
poetry run pytest

# 代码格式化
poetry run black app/ && poetry run ruff check app/
```

### 团队协作
- 查看任务: 使用 TaskList 工具
- 分配任务: 使用 TaskUpdate 设置 owner
- 成员沟通: 使用 SendMessage
- 派发成员: 使用 Agent 工具
