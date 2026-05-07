---
name: team-runtime-snapshot
description: 团队运行时配置快照 - 记录当前活跃团队的运行时状态
---

# 团队运行时配置快照

## 说明

此目录保存 Vigor 项目团队的运行时配置快照,便于日后查看和追溯。

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

### 与系统目录的关系

**系统运行时目录**(由 Claude Code 管理):
- `~/.claude/teams/vigor-dev-team/` - 活跃团队的实时配置
- `~/.claude/tasks/vigor-dev-team/` - 任务实时状态

**项目归档目录**(手动同步):
- `.claude/teams/vigor-dev-team/` - 团队配置快照
- `.claude/tasks/vigor-dev-team/` - 任务状态快照

### 同步命令

当需要更新项目内的快照时,可以使用以下命令:

```bash
# 同步团队配置
cp ~/.claude/teams/vigor-dev-team/config.json .claude/teams/vigor-dev-team/config.json

# 同步任务状态
cp ~/.claude/tasks/vigor-dev-team/*.json .claude/tasks/vigor-dev-team/
```

### 使用场景

- 项目交接时查看历史团队结构
- 追溯团队成员的 prompt 和职责
- 分析任务执行流程
- 为新项目参考团队配置

### 注意事项

- **运行时读写仍然使用系统目录** (`~/.claude/`)
- 项目目录只是**快照归档**,修改不会影响运行时
- 需要手动同步,建议在团队完成阶段性工作后同步一次
