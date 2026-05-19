#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_DIR="$ROOT_DIR/.vigor-dev"
LOG_DIR="$RUNTIME_DIR/logs"
PID_DIR="$RUNTIME_DIR/pids"

API_PORT="${API_PORT:-8000}"
CLIENT_PORT="${CLIENT_PORT:-3000}"

info() {
  printf '\033[1;34m[info]\033[0m %s\n' "$*"
}

status_line() {
  local name="$1"
  local pid_file="$PID_DIR/${name}.pid"

  if [[ ! -f "$pid_file" ]]; then
    printf '%-16s %s\n' "$name" "未由脚本启动"
    return
  fi

  local pid
  pid="$(cat "$pid_file")"
  if kill -0 "$pid" >/dev/null 2>&1; then
    printf '%-16s %s\n' "$name" "运行中 (PID ${pid})"
  else
    printf '%-16s %s\n' "$name" "PID 文件存在但进程已退出"
  fi
}

port_line() {
  local name="$1"
  local port="$2"
  if lsof -nP -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    printf '%-16s %s\n' "$name" "端口 ${port} 已监听"
  else
    printf '%-16s %s\n' "$name" "端口 ${port} 未监听"
  fi
}

main() {
  info "脚本管理的本地进程"
  status_line "api"
  status_line "celery-worker"
  status_line "celery-beat"
  status_line "client"

  printf '\n'
  info "端口状态"
  port_line "后端 API" "$API_PORT"
  port_line "前端 Vite" "$CLIENT_PORT"

  printf '\n'
  info "日志目录"
  printf '%s\n' "$LOG_DIR"
}

main "$@"
