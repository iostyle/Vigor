---
name: team-runtime-snapshot
description: 团队运行时配置快照 - 记录当前活跃团队的运行时状态
---

# 团队运行时配置快照

## 说明

此目录保存 Vigor 项目团队的运行时配置**快照**,作为项目内的权威归档,便于追溯和版本控制。

### 目录结构

```
.claude/
├── teams/
│   └── vigor-dev-team/
│       └── config.json          # 团队配置(成员、角色、prompt等)
└── tasks/
    └── vigor-dev-team/
        ├── 1.json               # Task #1 数据
        ├── 2.json               # Task #2 数据
        ├── 3.json               # Task #3 数据
        └── 4.json               # Task #4 数据
```

### 重要说明:关于运行时位置

**Claude Code 的团队与任务运行时数据由系统固定存放在 `~/.claude/` 下**,目前无法通过配置迁移到项目目录。原因是团队状态和任务状态需要跨项目、跨会话被 Claude Code 统一管理。

因此本项目采用"运行时 + 项目快照"的方式:

| 用途 | 位置 | 说明 |
|------|------|------|
| 运行时读写(系统自动管理) | `~/.claude/teams/vigor-dev-team/` | Claude Code 实时读写 |
| 运行时读写(系统自动管理) | `~/.claude/tasks/vigor-dev-team/` | Claude Code 实时读写 |
| 项目归档(权威来源) | `.claude/teams/vigor-dev-team/` | git 追踪,可移交 |
| 项目归档(权威来源) | `.claude/tasks/vigor-dev-team/` | git 追踪,可移交 |

**项目目录是权威来源** - 新环境拉取项目时,可以从 `.claude/` 下的快照重建团队。

### 同步命令

阶段性工作完成后,运行以下命令将运行时状态同步到项目目录:

```bash
# 同步团队配置
cp "$HOME/.claude/teams/vigor-dev-team/config.json" .claude/teams/vigor-dev-team/config.json

# 同步任务状态
cp "$HOME/.claude/tasks/vigor-dev-team/"*.json .claude/tasks/vigor-dev-team/

# 提交到 git
git add .claude/ && git commit -m "chore: sync team runtime snapshot"
```

### 使用场景

- **项目交接**: 新开发者拉取项目后,能看到完整团队结构和任务历史
- **追溯历史**: 查看每个团队成员的 prompt 和职责演变
- **版本控制**: 通过 git log 追踪团队配置变化
- **跨环境迁移**: 在新机器上通过快照快速重建团队

### 注意事项

- **实际读写发生在系统目录** - 不要直接修改 `.claude/teams/` 下的 JSON 期望影响运行时
- **修改后需要手动同步** - 团队状态变更后,需要运行同步命令才能提交到 git
- **建议同步时机**: 每完成一个里程碑任务后同步一次

