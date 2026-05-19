#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PID_DIR="$ROOT_DIR/.vigor-dev/pids"

info() {
  printf '\033[1;34m[info]\033[0m %s\n' "$*"
}

warn() {
  printf '\033[1;33m[warn]\033[0m %s\n' "$*"
}

stop_pid() {
  local name="$1"
  local pid_file="$2"
  local pid
  pid="$(cat "$pid_file")"

  if ! kill -0 "$pid" >/dev/null 2>&1; then
    warn "${name} 已不在运行"
    rm -f "$pid_file"
    return
  fi

  info "停止 ${name} (PID ${pid})"
  kill "$pid" >/dev/null 2>&1 || true

  for _ in $(seq 1 10); do
    if ! kill -0 "$pid" >/dev/null 2>&1; then
      rm -f "$pid_file"
      return
    fi
    sleep 1
  done

  warn "${name} 未正常退出,执行强制停止"
  kill -9 "$pid" >/dev/null 2>&1 || true
  rm -f "$pid_file"
}

main() {
  if [[ ! -d "$PID_DIR" ]]; then
    info "没有找到脚本管理的本地进程"
    return
  fi

  shopt -s nullglob
  local pid_files=("$PID_DIR"/*.pid)
  if [[ ${#pid_files[@]} -eq 0 ]]; then
    info "没有找到脚本管理的本地进程"
    return
  fi

  for pid_file in "${pid_files[@]}"; do
    local name
    name="$(basename "$pid_file" .pid)"
    stop_pid "$name" "$pid_file"
  done

  info "本地进程已停止。PostgreSQL 和 Redis 默认保留运行。"
}

main "$@"
