#!/usr/bin/env bash
# SessionStart hook 入口:
#  1) 修复 ~/.claude/{teams,tasks}/vigor-dev-team 符号链接
#  2) 把团队 config 的 leadSessionId 更新为当前 session_id,
#     让新会话自动接管 vigor-dev-team 作为 team-lead
# 幂等,静默,只在真正修复了什么时输出一行
set -euo pipefail

PROJECT_DIR="${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
TEAM_NAME="vigor-dev-team"
TEAM_CONFIG="$PROJECT_DIR/.claude/teams/$TEAM_NAME/config.json"

ensure_link() {
  local kind="$1"
  local src="$PROJECT_DIR/.claude/$kind/$TEAM_NAME"
  local dst="$HOME/.claude/$kind/$TEAM_NAME"

  [ -d "$src" ] || return 0
  mkdir -p "$HOME/.claude/$kind"

  if [ -L "$dst" ] && [ "$(readlink "$dst")" = "$src" ]; then
    return 0
  fi

  ln -sfn "$src" "$dst"
  echo "[bootstrap] relinked $dst -> $src" >&2
}

takeover_team_lead() {
  local hook_input session_id
  hook_input="$(cat 2>/dev/null || true)"
  session_id="$(printf '%s' "$hook_input" | jq -r '.session_id // empty' 2>/dev/null || true)"

  [ -n "$session_id" ] || return 0
  [ -f "$TEAM_CONFIG" ] || return 0

  local current
  current="$(jq -r '.leadSessionId // empty' "$TEAM_CONFIG" 2>/dev/null || true)"
  [ "$current" != "$session_id" ] || return 0

  local tmp
  tmp="$(mktemp)"
  jq --arg sid "$session_id" '.leadSessionId = $sid' "$TEAM_CONFIG" > "$tmp" && mv "$tmp" "$TEAM_CONFIG"
  echo "[bootstrap] vigor-dev-team lead session -> $session_id" >&2
}

ensure_link teams
ensure_link tasks
takeover_team_lead
