#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVER_DIR="$ROOT_DIR/vigor-server"
CLIENT_DIR="$ROOT_DIR/vigor-client"
RUNTIME_DIR="$ROOT_DIR/.vigor-dev"
LOG_DIR="$RUNTIME_DIR/logs"
PID_DIR="$RUNTIME_DIR/pids"

API_PORT="${API_PORT:-8000}"
CLIENT_PORT="${CLIENT_PORT:-3000}"
API_HOST="${API_HOST:-0.0.0.0}"
CLIENT_HOST="${CLIENT_HOST:-0.0.0.0}"

info() {
  printf '\033[1;34m[info]\033[0m %s\n' "$*"
}

warn() {
  printf '\033[1;33m[warn]\033[0m %s\n' "$*"
}

fail() {
  printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2
  exit 1
}

is_pid_alive() {
  local pid="$1"
  [[ -n "$pid" ]] && kill -0 "$pid" >/dev/null 2>&1
}

stop_service() {
  local name="$1"
  local pid_file="$PID_DIR/${name}.pid"
  if [[ ! -f "$pid_file" ]]; then
    warn "${name} 没有 PID 文件,跳过停止"
    return
  fi

  local pid
  pid="$(cat "$pid_file")"
  if ! is_pid_alive "$pid"; then
    warn "${name} 已不在运行"
    rm -f "$pid_file"
    return
  fi

  info "停止 ${name} (PID ${pid})"
  kill "$pid" >/dev/null 2>&1 || true
  for _ in $(seq 1 10); do
    if ! is_pid_alive "$pid"; then
      rm -f "$pid_file"
      return
    fi
    sleep 1
  done

  warn "${name} 未正常退出,执行强制停止"
  kill -9 "$pid" >/dev/null 2>&1 || true
  rm -f "$pid_file"
}

start_process() {
  local name="$1"
  local workdir="$2"
  local command="$3"
  local pid_file="$PID_DIR/${name}.pid"
  local log_file="$LOG_DIR/${name}.log"

  mkdir -p "$LOG_DIR" "$PID_DIR"
  info "启动 ${name}"
  (
    cd "$workdir"
    nohup bash -lc "$command" >"$log_file" 2>&1 &
    printf '%s' "$!" >"$pid_file"
  )
}

restart_service() {
  local name="$1"
  stop_service "$name"
  case "$name" in
    api)
      start_process "api" "$SERVER_DIR" "poetry run uvicorn app.main:app --host ${API_HOST} --port ${API_PORT}"
      ;;
    client)
      start_process "client" "$CLIENT_DIR" "npm run dev -- --host ${CLIENT_HOST} --port ${CLIENT_PORT}"
      ;;
    celery-worker)
      start_process "celery-worker" "$SERVER_DIR" "poetry run celery -A app.celery_app worker -n vigor-worker@%h -Q crawler,processor,updater --loglevel=info"
      ;;
    celery-beat)
      start_process "celery-beat" "$SERVER_DIR" "poetry run celery -A app.celery_app beat --loglevel=info --schedule '$RUNTIME_DIR/celerybeat-schedule.db'"
      ;;
    *)
      fail "未知服务: ${name}"
      ;;
  esac
}

main() {
  local target="${1:-all}"
  case "$target" in
    all)
      restart_service "api"
      restart_service "celery-worker"
      restart_service "celery-beat"
      restart_service "client"
      ;;
    api)
      restart_service "api"
      ;;
    client)
      restart_service "client"
      ;;
    worker | celery-worker)
      restart_service "celery-worker"
      ;;
    beat | celery-beat)
      restart_service "celery-beat"
      ;;
    *)
      fail "用法: ./scripts/dev-restart.sh [all|api|client|worker|beat]"
      ;;
  esac
}

main "$@"
