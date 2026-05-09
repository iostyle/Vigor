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


# andrej-karpathy-skills

四个原则，集中在一个文件中，直接解决这些问题：

| 原则 | 解决什么问题 |
|-----------|-----------|
| **编码前思考** | 错误假设、隐藏困惑、缺少权衡 |
| **简洁优先** | 过度复杂、臃肿抽象 |
| **精准修改** | 无关编辑、触碰不应碰的代码 |
| **目标驱动执行** | 通过测试优先、可验证的成功标准 |

## 四个原则详解

### 1. 编码前思考

**不要假设。不要隐藏困惑。呈现权衡。**

LLM 经常默默选择一种解释然后执行。这个原则强制明确推理：

- **明确说明假设** — 如果不确定，询问而不是猜测
- **呈现多种解释** — 当存在歧义时，不要默默选择
- **适时提出异议** — 如果存在更简单的方法，说出来
- **困惑时停下来** — 指出不清楚的地方并要求澄清

### 2. 简洁优先

**用最少的代码解决问题。不要过度推测。**

对抗过度工程的倾向：

- 不要添加要求之外的功能
- 不要为一次性代码创建抽象
- 不要添加未要求的"灵活性"或"可配置性"
- 不要为不可能发生的场景做错误处理
- 如果 200 行代码可以写成 50 行，重写它

**检验标准：** 资深工程师会觉得这过于复杂吗？如果是，简化。

### 3. 精准修改

**只碰必须碰的。只清理自己造成的混乱。**

编辑现有代码时：

- 不要"改进"相邻的代码、注释或格式
- 不要重构没坏的东西
- 匹配现有风格，即使你更倾向于不同的写法
- 如果注意到无关的死代码，提一下 —— 不要删除它

当你的改动产生孤儿代码时：

- 删除因你的改动而变得无用的导入/变量/函数
- 不要删除预先存在的死代码，除非被要求

**检验标准：** 每一行修改都应该能直接追溯到用户的请求。

### 4. 目标驱动执行

**定义成功标准。循环验证直到达成。**

将指令式任务转化为可验证的目标：

| 不要这样做... | 转化为... |
|--------------|-----------------|
| "添加验证" | "为无效输入编写测试，然后让它们通过" |
| "修复 bug" | "编写重现 bug 的测试，然后让它通过" |
| "重构 X" | "确保重构前后测试都能通过" |

对于多步骤任务，说明一个简短的计划：

```
1. [步骤] → 验证: [检查]
2. [步骤] → 验证: [检查]
3. [步骤] → 验证: [检查]
```

强有力的成功标准让 LLM 能够独立循环执行。弱标准（"让它工作"）需要不断澄清。