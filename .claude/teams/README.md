---
name: team-runtime-config
description: 团队运行时配置 - 团队和任务数据的权威存储位置
---

# 团队运行时配置

## 说明

此目录是 Vigor 项目团队和任务数据的**权威存储位置**,所有读写实际发生在此,并通过 git 追踪。

## 目录结构

```
.claude/
├── teams/
│   └── vigor-dev-team/
│       ├── config.json          # 团队配置(成员、角色、prompt 等)
│       └── inboxes/             # 成员消息收件箱
│           ├── team-lead.json
│           ├── architect.json
│           └── ...
└── tasks/
    └── vigor-dev-team/
        ├── 1.json               # 任务数据
        ├── 2.json
        └── ...
```

## 存储位置机制

Claude Code 默认读写 `~/.claude/teams/<team-name>` 和 `~/.claude/tasks/<team-name>`,本项目通过**符号链接**将这两个系统路径指向项目目录:

```
~/.claude/teams/vigor-dev-team  →  .claude/teams/vigor-dev-team
~/.claude/tasks/vigor-dev-team  →  .claude/tasks/vigor-dev-team
```

这样 Claude Code 写入时数据自动落在项目目录,随 git 追踪,不需要手动同步。

## 新环境部署

克隆仓库到新机器后,执行以下命令重建符号链接:

```bash
cd <project-dir>

# 确保系统目录存在
mkdir -p ~/.claude/teams ~/.claude/tasks

# 重建符号链接(-f 覆盖已有链接)
ln -sfn "$PWD/.claude/teams/vigor-dev-team" ~/.claude/teams/vigor-dev-team
ln -sfn "$PWD/.claude/tasks/vigor-dev-team" ~/.claude/tasks/vigor-dev-team

# 验证
ls -la ~/.claude/teams/vigor-dev-team ~/.claude/tasks/vigor-dev-team
```

## 验证链接状态

```bash
# 应看到 lrwxr-xr-x(链接) 而非 drwxr-xr-x(普通目录)
ls -la ~/.claude/teams/vigor-dev-team

# 通过链接读应等同于直接读项目目录
diff <(cat ~/.claude/teams/vigor-dev-team/config.json) \
     <(cat .claude/teams/vigor-dev-team/config.json)
```

## 注意事项

- **不要手动删除** `~/.claude/teams/vigor-dev-team` 和 `~/.claude/tasks/vigor-dev-team`,否则数据会被系统重新生成到 `~/.claude/` 下
- **移动项目目录后需要重建链接**:符号链接是绝对路径
- **git clone 后首次使用前必须重建链接**:git 不追踪 `~/.claude/` 下的链接
- **不要把 .git 目录同步到系统链接**:只链接 `.claude/teams/<team>` 和 `.claude/tasks/<team>`,不要链接整个 `.claude/`

## 使用场景

- **项目交接**: 新开发者克隆后重建链接即可继续工作
- **追溯历史**: `git log .claude/` 查看团队配置演变
- **跨机器开发**: 团队状态和任务跟着项目走
